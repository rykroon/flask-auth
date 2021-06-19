from flask import g, request


class BaseThrottle:
    
    def get_ident(self):
        return g.user or request.remote_addr or '127.0.0.1'

    def get_cache_key(self):
        return 'throttle:{}'.format(self.get_ident())

    def allow_request(self):
        pass

    def retry_after(self):
        pass



