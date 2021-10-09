from functools import wraps
import time
from flask import g, request
from werkzeug.exceptions import TooManyRequests


class SlidingWindow(list):

    def add_request(self, now):
        self.insert(0, now)

    def slide_window(self, duration, now):
        while self and self[-1] <= now - duration:
            self.pop()


def throttle(throttle_class, seconds=None, minutes=None, hours=None, days=None):
    durations = {
        'seconds': seconds,
        'minutes': minutes,
        'hours': hours,
        'days': days
    }

    durations = {k: v for k, v in durations.items() if v is not None}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for period, num in durations.items():
                rate = '{}/{}'.format(num, period[0])
                throttle = throttle_class(rate)
                if not throttle.allow_request():
                    raise TooManyRequests(retry_after=throttle.retry_after())
            return func(*args, **kwargs)
        return wrapper
    return decorator


class BaseThrottle:

    scope = None

    def __init__(self, rate):
        num, period = rate.split('/')
        self.num_requests = int(num)
        self.duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]

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

        cache_key = 'throttle:{path}:{scope}:{ident}{duration}'.format(
            path=request.path,
            scope=self.scope,
            ident=self.get_identifier(),
            duration=self.duration
        )

        self.history = self.cache.get(cache_key) or SlidingWindow()
        self.now = time.time()

        # "slide" the window based on the max duration
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

