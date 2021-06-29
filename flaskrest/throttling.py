from functools import wraps
import time
from cachelib import SimpleCache
from flask import g
from werkzeug.exceptions import TooManyRequests


class Throttle:

    cache = SimpleCache()

    def __init__(self, scopes, second=None, minute=None, hour=None, day=None):
        self.scopes = scopes

        self.durations = {
            86400: day,
            3600: hour,
            60: minute,
            1: second
        }

        # Remove durations without a specified number of requests
        self.durations = {k: v for k, v in self.durations.items() if v is not None}

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.allow_request():
                raise TooManyRequests
            return func(*args, **kwargs)
        return wrapper

    def allow_request(self):
        # If the scopes do not match then the request
        # will not be throttled. 
        for scope in self.scopes:
            if scope not in g.auth.scopes:
                return True

        cache_key = 'throttle:{scopes}:{user}'.format(
            scopes=''.join(self.scopes),
            user=g.user.identifier
        )

        history = self.cache.get(cache_key) or []
        now = time.time()

        # "slide" the window based on the max duration
        max_duration = max(self.durations)
        while history and history[-1] <= now - max_duration:
            history.pop()

        end_index = len(history) - 1
        for duration, num_requests in self.durations.items():    
            while end_index >= 0 and history[end_index] <= now - duration:
                end_index -= 1

            if end_index + 1 >= num_requests:
                return False

        history.insert(0, now)
        self.cache.set(cache_key, history, max_duration)
        return True

    def retry_after(self):
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1
        if available_requests <= 0:
            return None

        return remaining_duration / float(available_requests)

