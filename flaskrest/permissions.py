from flask import g, request


SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class BasePermission:
    def has_permission(self):
        raise NotImplementedError

    def has_object_permission(self, obj):
        raise NotImplementedError


class AllowAny(BasePermission):
    def has_permission(self):
        return True


class IsAuthneticated(BasePermission):
    def has_permission(self):
        return g.user is not None


class IsAuthneticatedOrReadOnly(BasePermission):
    def has_permission(self):
        return request.method in SAFE_METHODS or g.user is not None