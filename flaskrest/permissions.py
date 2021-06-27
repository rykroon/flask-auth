from functools import wraps
from flask import g
from werkzeug.exceptions import Forbidden


class Permission:
    def __init__(self, *scopes):
        self.scopes = scopes

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.has_permission():
                raise Forbidden
            return func(*args, **kwargs)
        return wrapper

    def has_permission(self):
        for scope in self.scopes:
            if scope not in g.auth.scopes:
                return False
        return True


allow_any = Permission()
is_authenticated = Permission('is_authenticated')
is_admin = Permission('is_admin')
