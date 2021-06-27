

class BaseAuthentication:
    @property
    def www_authenticate(self):
        raise NotImplementedError

    def authenticate(self):
        raise NotImplementedError