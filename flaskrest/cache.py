


class BaseCache:

    def get(self, key, default):
        raise NotImplementedError

    def set(self, key, value, timeout):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError