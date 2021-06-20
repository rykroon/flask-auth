import time
from flask import current_app, g, request


def get_remote_addr():
    if request.access_route:
        return ''.join(request.access_route)

    return request.remote_addr


class BaseThrottle:

    rate = None
    scope = None

    def __init__(self):
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def parse_rate(self, rate):
        num, period = rate.split('/')
        num_requests = int(num)
        duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_requests, duration)
    
    def get_ident(self):
        return None

    def get_cache_key(self):
        return 'throttle:{}:{}'.format(self.scope, self.get_ident())

    def get_from_cache(self, key, default=None):
        raise NotImplementedError

    def set_to_cache(self, key, value, timeout):
        raise NotImplementedError

    def allow_request(self):
        raise NotImplementedError

    def retry_after(self):
        raise NotImplementedError


class SlidingWindowThrottle(BaseThrottle):

    def allow_request(self):
        if self.rate is None:
            return True

        #if the get_ident() function returns None
        # then there is no identity to rate limit so return True
        if self.get_ident() is None:
            return True

        self.key = self.get_cache_key()

        self.history = self.get_from_cache(self.key, [])
        self.now = time.time()

        # "slide" the window
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            return self.throttle_failure()

        return self.throttle_success()

    def throttle_success(self):
        self.history.insert(0, self.now)
        self.set_to_cache(self.key, self.history, self.duration)
        return True

    def throttle_failure(self):
        return False

    def retry_after(self):
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1
        if available_requests <= 0:
            return None

        return remaining_duration / float(available_requests)


class AnonThrottle(SimpleRateThrottle):
    scope = 'anon'

    def get_ident(self):
        if g.user:
            return None

        return get_remote_addr()


class UserThrottle(SimpleRateThrottle):
    scope = 'user'

    def get_ident(self):
        return g.user