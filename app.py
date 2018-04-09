from flask import Flask
from flask_restful import Api

from models import db
from resources.user import UserREST, UserRegisterREST, UserAuthorizationREST, UserTokenAuthorizeREST
from config import config


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///course.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = config.SECRET_KEY
db.init_app(app)


api = Api(app)


api.add_resource(UserREST, '/users')
api.add_resource(UserRegisterREST, '/users/register')
api.add_resource(UserAuthorizationREST, '/users/authorize')
api.add_resource(UserTokenAuthorizeREST, '/users/refreshtoken')

if __name__ == '__main__':
    app.run(debug=True)
