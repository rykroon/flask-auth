from functools import update_wrapper
from flask import g
from werkzeug.exceptions import Forbidden


class BasePermission:

    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func
    
    def __call__(self, *args, **kwargs):
        if not self.has_permission():
            raise Forbidden
        return self.func(*args, **kwargs)

    def has_permission(self):
        raise NotImplementedError


class AllowAny(BasePermission):
    def has_permission(self):
        return True


class IsAuthenticated(BasePermission):
    def has_permission(self):
        return g.user.is_authenticated


class IsAdmin(BasePermission):
    def has_permission(self):
        return g.user.is_admin


