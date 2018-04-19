from flask import Flask
from flask_restful import Api

from models import db
from resources.user import UserREST, UserRegisterREST, UserAuthorizationREST, UserTokenAuthorizeREST
from resources.regex import RegexPostsREST
from config import config


DB_URI = f'postgresql+psycopg2://{config.POSTGRES_USER}:{config.POSTGRES_PW}@{config.POSTGRES_URL}/{config.POSTGRES_DB}'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = config.SECRET_KEY
db.init_app(app)


api = Api(app)


api.add_resource(UserREST, '/users')
api.add_resource(UserRegisterREST, '/users/register')
api.add_resource(UserAuthorizationREST, '/users/authorize')
api.add_resource(UserTokenAuthorizeREST, '/users/refresh_token')
api.add_resource(RegexPostsREST, '/regex/posts')


if __name__ == '__main__':
    app.run(debug=True)
