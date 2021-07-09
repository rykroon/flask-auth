from cachelib import SimpleCache
from flask import Flask
from flask.views import MethodView

from flaskauth import AuthenticationMiddleware
from flaskauth.permissions import AllowAny, IsAuthenticated
from flaskauth.throttling import SimpleThrottle, AnonThrottle

app = Flask(__name__)

@app.before_request
def init_middleware():
    auth_mw = AuthenticationMiddleware(
        authentication_classes=[]
    )
    auth_mw()


cache = SimpleCache()

class MySimpleThrottle(SimpleThrottle):
    minute = 10
    second = 1

    @property
    def cache(self):
        return cache


@app.route('/', methods=['get'])
@AllowAny
@MySimpleThrottle
def root():
    return "OK"


if __name__ == '__main__':
    app.run()