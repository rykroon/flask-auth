from base64 import b64decode
from flask import request, g
from werkzeug.exceptions import BadRequest, Unauthorized


"""
    Parts of Authentication

    Location of the authorization parameter.
        - headers
        - body
        - query parameters

    The name of the parameter.
    
    The method of Authorization
        - Basic
        - Bearer (Token)
        - other
"""


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


class SchemeAuthentication(BaseAuthentication):
    scheme = None
    realm = None

    @property
    def www_authenticate(self):
        realm = self.realm or request.host_url
        return "{} realm={}".format(self.scheme, realm)

    def authenticate(self):
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            return None, None

        scheme, _, credentials = authorization_header.partition(' ')
        if not credentials:
            raise BadRequest('Invalid Authorization header.')

        if scheme.lower() != self.scheme.lower():
            return None, None

        return self.validate_credentials(credentials)

    def validate_credentials(self, credentials):
        raise NotImplementedError


class BasicAuthentication(SchemeAuthentication):
    scheme = 'Basic'
    
    def validate_credentials(self, credentials):
        decoded_credentials = b64decode(credentials)
        username, _, password = decoded_credentials.partition(':')

        user = self.get_user(username, password)
        if not user:
            raise Unauthorized(
                'Invalid username or password.',
                www_authenticate=self.www_authenticate
            )

        return user
        

class AuthCredentials:
    def __init__(self, scopes):
        self.scopes = scopes


class BaseUser:
    
    @property
    def is_authenticated(self):
        raise NotImplementedError

