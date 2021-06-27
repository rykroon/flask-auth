from functools import wraps
import time
from flask import g
from werkzeug.exceptions import TooManyRequests


class Throttle:
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

        cache_key = 'throttle:{user}:{scopes}'.format(
            user=g.user.identifier, 
            scopes=''.join(self.scopes)
        )

        history = cache.get(cache_key, [])
        now = time.time()

        # "slide" the window based on the max duration
        max_duration = max(self.durations)
        while history and history[-1] <= now - max_duration:
            history.pop()

        for duration, num_requests in self.durations.items():
            end_index = len(history) - 1
            while history and history[end_index] <= now - duration:
                end_index -= 1

            if len(history[:end_index]) + 1 >= num_requests:
                return False

        history.insert(0, now)
        cache.set(cache_key, history, max_duration)
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

