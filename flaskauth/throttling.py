from functools import wraps
import time
from flask import g
from werkzeug.exceptions import TooManyRequests


class SlidingWindow(list):

    def add_request(self, now=None):
        now = now or time.time()
        self.insert(0, now)

    def slide_window(self, duration, now=None):
        now = now or time.time()
        while self and self[-1] <= now - duration:
            self.pop()

    def copy(self):
        return self.__class__(super().copy())


def throttle(throttle_class, **throttle_kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            throttle = throttle_class(**throttle_kwargs)
            if not throttle.allow_request():
                raise TooManyRequests(retry_after=throttle.retry_after())
            return func(*args, **kwargs)
        return wrapper
    return decorator


class BaseThrottle:

    scope = None

    def __init__(self, second=None, minute=None, hour=None, day=None):
        
        self.durations = {
            86400: day,
            3600: hour,
            60: minute,
            1: second
        }

        # Remove durations without a specified number of requests
        self.durations = {k: v for k, v in self.durations.items() if v is not None}

    def allow_request(self):
        raise NotImplementedError

    def retry_after(self):
        raise NotImplementedError


class SimpleThrottle(BaseThrottle):

    @property
    def cache(self):
        raise NotImplementedError

    def get_identifier(self):
        return g.user.identifier

    def allow_request(self):
        if not self.durations:
            return True

        cache_key = 'throttle:{scope}:{identifier}'.format(
            scope=self.scope,
            identifier=self.get_identifier()
        )

        self.history = self.cache.get(cache_key) or SlidingWindow()
        self.now = time.time()

        # "slide" the window based on the max duration
        max_duration = max(self.durations)
        self.history.slide_window(max_duration)

        for duration, num_requests in self.durations.items():    
            temp_history = self.history.copy()
            temp_history.slide_window(duration, self.now)

            if len(temp_history) >= num_requests:
                self.throttled_history = temp_history
                self.throttled_duration = duration
                return False

        self.history.add_request(self.now)
        self.cache.set(cache_key, self.history, max_duration)
        return True

    def retry_after(self):
        if self.throttled_history:
            return self.throttled_duration - (self.now - self.throttled_history[-1])
        return self.throttled_duration


class AnonThrottle(SimpleThrottle):

    scope = 'anon'

    def allow_request(self):
        if not g.user.is_authenticated:
            return super().allow_request()
        return True

