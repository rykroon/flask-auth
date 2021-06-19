from flask.views import MethodView


class APIView(MethodView):

    authentication_classes = []
    permission_classes = []
    throttle_classes = []

    def dispatch_request(self, *args, **kwargs):
        self.initial()
        return super().dispatch_request(*args, **kwargs)

    def initial(self):
        self.perform_authentication()
        self.check_permissions()
        self.check_throttles()

    def get_authenticators(self):
        return [auth() for auth in self.authentication_classes]

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def get_throttles(self):
        return [throttle() for throttle in self.throttle_classes]

    def perform_authentication(self):
        pass

    def check_permissions(self):
        pass

    def check_throttles(self):
        pass

    