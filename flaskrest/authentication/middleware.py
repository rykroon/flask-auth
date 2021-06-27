from flask import g
from flaskrest.authentication.models import UnauthenticatedUser, AuthCredentials


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

        g.user = UnauthenticatedUser()
        g.auth = AuthCredentials(scopes=['*', 'anonymous'])

    def get_authenticators(self):
        return [auth() for auth in self.authentication_classes]