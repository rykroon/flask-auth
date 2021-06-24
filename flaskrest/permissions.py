from functools import wraps

from flask import g, request
from werkzeug.exceptions import Forbidden


def permission(scopes):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for scope in scopes:
                if scope not in g.auth.scopes:
                    raise Forbidden
            return func(*args, **kwargs)
        return wrapper
    return decorator


allow_any = permission('*')
is_authenticated = permission('is_authenticated')
is_admin = permission('is_admin')
