from functools import wraps
from flask import g, request
from werkzeug.exceptions import Forbidden


SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


def permission(permission_class, **permission_kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(args, **kwargs):
            perm = permission_class(**permission_kwargs)
            if not perm.has_permission():
                raise Forbidden
            return func(*args, **kwargs)
        return wrapper
    return decorator


class BasePermission:
    def has_permission(self):
        raise NotImplementedError


class AllowAny(BasePermission):
    def has_permission(self):
        return True


class IsAuthenticated(BasePermission):
    def has_permission(self):
        return bool(g.user and g.user.is_authenticated)


class IsAdmin(BasePermission):
    def has_permission(self):
        return bool(g.user and g.user.is_admin)


class IsAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self):
        return bool(request.method in SAFE_METHODS or g.user and g.user.is_authenticated)


allow_any = permission(AllowAny)
is_authenticated = permission(IsAuthenticated)
is_admin = permission(IsAdmin)
is_authenticated_or_read_only = permission(IsAuthenticatedOrReadOnly)
