from flask import request, g
from werkzeug.exceptions import BadRequest, Unauthorized


class AuthenticationMiddleware:
    def __init__(self, authentication_classes):
        self.authentication_classes = authentication_classes

    def __call__(self):
        for auth in self.get_authenticators():
            try:
                user_auth_tuple = auth.authenticate()
            except Exception as e:
                raise e
            
            if user_auth_tuple is not None:
                g.user, g.auth = user_auth_tuple
                return

        g.user = None
        g.auth = None

    def get_authenticators(self):
        return [auth() for auth in self.authentication_classes]


class BaseAuthentication:
    def authenticate(self):
        raise NotImplementedError
        

class AuthCredentials:
    def __init__(self, scopes):
        self.scopes = scopes


class BaseUser:

    @property
    def identifier(self):
        raise NotImplementedError

    @property
    def is_authenticated(self):
        raise NotImplementedError

    @property
    def is_admin(self):
        raise NotImplementedError


class SimpleUser(BaseUser):
    def __init__(self, identifier):
        self.identifier = identifier

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, value):
        self._identifier = value

    @property
    def is_authenticated(self):
        return True

    @property
    def is_admin(self):
        return False


class UnauthenticatedUser(BaseUser):
    @property
    def identifier(self):
        if request.access_route:
            return ''.join(request.access_route)

        return request.remote_addr

    @property
    def is_authenticated(self):
        return False

    @property
    def is_admin(self):
        return False
