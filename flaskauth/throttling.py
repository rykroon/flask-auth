from functools import update_wrapper
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


class BaseThrottle:

    second = None
    minute = None
    hour = None
    day = None

    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

        self.durations = {
            86400: self.day,
            3600: self.hour,
            60: self.minute,
            1: self.second
        }

        # Remove durations without a specified number of requests
        self.durations = {k: v for k, v in self.durations.items() if v is not None}

    def __call__(self, *args, **kwargs):
        allowed, retry_after = self.allow_request()
        if not allowed:
            raise TooManyRequests(retry_after=retry_after)
        return self.func(*args, **kwargs)

    def allow_request(self):
        raise NotImplementedError


class SimpleThrottle(BaseThrottle):

    @property
    def cache(self):
        raise NotImplementedError

    def allow_request(self):
        """
            Returns a 2-tuple of (allow, retry_after)
        """
        if not self.durations:
            return True, None

        cache_key = 'throttle:{scope}:{user}'.format(
            scope=self.__class__.__name__,
            user=g.user.identifier
        )

        history = self.cache.get(cache_key) or SlidingWindow()
        now = time.time()

        # "slide" the window based on the max duration
        max_duration = max(self.durations)
        history.slide_window(max_duration)

        for duration, num_requests in self.durations.items():    
            temp_history = history.copy()
            temp_history.slide_window(duration, now)

            if len(temp_history) >= num_requests:
                if temp_history:
                    remaining_duration = duration - (now - temp_history[-1])
                else:
                    remaining_duration = duration

                return False, remaining_duration

        history.add_request(now)
        self.cache.set(cache_key, history, max_duration)
        return True, None


class AnonThrottle(SimpleThrottle):

    def allow_request(self):
        if not g.user.is_authenticated:
            return super().allow_request()
        return True

