from functools import wraps
import time
from cachelib import NullCache
from flask import g, request
from werkzeug.exceptions import TooManyRequests


class SlidingWindow(list):

    def add_request(self, timestamp):
        self.insert(0, timestamp)

    def slide_window(self, duration, timestamp):
        while self and self[-1] <= timestamp - duration:
            self.pop()


def throttle(throttle_class, per_sec=None, per_min=None, per_hr=None, per_day=None):
    rates = [
        (per_sec, 1),
        (per_min, 60),
        (per_hr, 3600),
        (per_day, 86400)
    ]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for num_of_requests, duration in rates:
                if num_of_requests is None:
                    continue

                throttle = throttle_class(num_of_requests, duration)
                if not throttle.allow_request():
                    raise TooManyRequests(retry_after=throttle.retry_after())

            return func(*args, **kwargs)
        return wrapper
    return decorator


class BaseThrottle:

    scope = None

    def __init__(self, num_of_requests, duration):
        self.num_requests = num_of_requests
        self.duration = duration

    def allow_request(self):
        raise NotImplementedError

    def retry_after(self):
        raise NotImplementedError


class SimpleThrottle(BaseThrottle):

    cache = NullCache()

    def get_identifier(self):
        return g.user.identifier

    def allow_request(self):

        cache_key = 'throttle:{path}:{scope}:{ident}{duration}'.format(
            path=request.path, # where
            scope=self.scope, # what
            ident=self.get_identifier(), # who
            duration=self.duration # which
        )

        self.history = self.cache.get(cache_key) or SlidingWindow()
        self.now = time.time()

        # "slide" the window based on the duration
        self.history.slide_window(self.duration, self.now)

        if len(self.history) >= self.num_requests:
            return False

        self.history.add_request(self.now)
        self.cache.set(cache_key, self.history, self.duration)
        return True

    def retry_after(self):
        if self.history:
            return self.duration - (self.now - self.history[-1])
        return self.duration


class AnonThrottle(SimpleThrottle):

    scope = 'anon'

    def allow_request(self):
        if not g.user.is_authenticated:
            return super().allow_request()
        return True

