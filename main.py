from cachelib import SimpleCache, RedisCache
from flask import Flask
from flask.views import MethodView

from flaskauth import AuthenticationMiddleware
from flaskauth.permissions import allow_any
from flaskauth.throttling import SimpleThrottle, throttle

app = Flask(__name__)

@app.before_request
def init_middleware():
    auth_mw = AuthenticationMiddleware(
        authentication_classes=[]
    )
    auth_mw()


cache = RedisCache()

class MySimpleThrottle(SimpleThrottle):

    @property
    def cache(self):
        return cache


@app.route('/', methods=['get'])
@allow_any
@throttle(MySimpleThrottle, block_time=3600, per_hr=9, per_min=3, per_sec=1)
def root():
    return "OK"


if __name__ == '__main__':
    app.run()