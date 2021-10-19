from functools import wraps
import time
from cachelib import NullCache
from flask import g, request
from werkzeug.utils import cached_property
from werkzeug.exceptions import TooManyRequests


class SlidingWindow(list):

    def __init__(self, duration):
        self.duration = duration

    def add_request(self, timestamp):
        self.insert(0, timestamp)

    def slide_window(self, timestamp):
        while self and self[-1] <= timestamp - self.duration:
            self.pop()


def throttle(throttle_class, per_sec=None, per_min=None, per_hr=None, per_day=None, block_time=None):
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

                throttle = throttle_class(num_of_requests, duration, block_time=block_time)
                if not throttle.allow_request():
                    raise TooManyRequests(retry_after=throttle.retry_after())

            return func(*args, **kwargs)
        return wrapper
    return decorator


class BaseThrottle:

    def allow_request(self):
        raise NotImplementedError

    def retry_after(self):
        raise NotImplementedError


class SimpleThrottle:

    cache = NullCache()
    scope = 'default'

    def __init__(self, num_of_requests, duration, block_time=None):
        self.num_requests = num_of_requests
        self.duration = duration
        self.block_time = block_time

    @cached_property
    def user(self):
        return g.user.identifier

    def allow_request(self):
        if self.is_blocking():
            return False

        cache_key = f'{request.path}:{self.user}:{self.duration}'
        self.history = self.cache.get(cache_key) or SlidingWindow(self.duration)
        self.now = time.time()
        self.history.slide_window(self.now)

        if len(self.history) >= self.num_requests:
            self.set_block_time()
            return False

        self.history.add_request(self.now)
        self.cache.set(cache_key, self.history, self.duration)
        return True

    def set_block_time(self):
        if self.block_time:
            self.cache.set(f"blocking:{self.user}", 1, self.block_time)

    def remaining_block_time(self):
        return self.cache._client.ttl(f"blocking:{self.user}")

    def is_blocking(self):
        return self.remaining_block_time() > 0

    def retry_after(self):
        block_time = self.remaining_block_time()
        if block_time > 0:
            return block_time
        
        if self.history:
            return self.duration - (self.now - self.history[-1])
        return self.duration


class AnonThrottle(SimpleThrottle):
    scope = 'anon'

    def allow_request(self):
        if g.user.is_authenticated:
            return True

        return super().allow_request()


class UserThrottle(SimpleThrottle):
    scope = 'user'

    def allow_request(self):
        if not self.user.is_authenticated:
            return True

        if not self.user.is_admin:
            return True
        
        return super().allow_request()


class AdminThrottle(SimpleThrottle):
    scope = 'admin'

    def allow_request(self):
        if not g.is_admin:
            return True
        return super().allow_request()

