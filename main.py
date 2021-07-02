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


SimpleThrottle.minute = 10
SimpleThrottle.second = 1


@app.route('/', methods=['get'])
@AllowAny
@SimpleThrottle
def root():
    return "OK"


if __name__ == '__main__':
    app.run()