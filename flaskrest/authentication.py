from base64 import b64decode
from flask import request
from werkzeug.exceptions import BadRequest, Unauthorized


class BaseAuthentication:
    scheme = None
    realm = None

    @property
    def www_authenticate(self):
        realm = self.realm or request.host_url
        return "{} realm={}".format(self.scheme, realm)

    def authenticate(self):
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            return None

        scheme, _, credentials = authorization_header.partition(' ')
        if not credentials:
            raise BadRequest('Invalid Authorization header.')

        if scheme.lower() != self.scheme.lower():
            return None

        return self.validate_credentials(credentials)

    def validate_credentials(self, credentials):
        raise NotImplementedError

    def get_user(self, **kwargs):
        raise NotImplementedError


class BasicAuthentication(BaseAuthentication):
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
        



