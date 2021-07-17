from cachelib import SimpleCache
from flask import Flask
from flask.views import MethodView

from flaskauth import AuthenticationMiddleware
from flaskauth.permissions import AllowAny
from flaskauth.throttling import SimpleThrottle, rate_limit

app = Flask(__name__)

@app.before_request
def init_middleware():
    auth_mw = AuthenticationMiddleware(
        authentication_classes=[]
    )
    auth_mw()


cache = SimpleCache()

class MySimpleThrottle(SimpleThrottle):

    @property
    def cache(self):
        return cache


@app.route('/', methods=['get'])
@AllowAny
@rate_limit(MySimpleThrottle, minute=10, second=1)
def root():
    return "OK"


if __name__ == '__main__':
    app.run()