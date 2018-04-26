from flask import Flask
from flask_restful import Api

from models import db
from resources.user import UserREST, UserExitREST, UserRegisterREST, UserAuthorizationREST, UserTokenAuthorizeREST
from resources.regex import (
    RegexREST, RegexEditREST, RegexCreateREST,
    RegexDeleteREST, RegexSearchREST, RegexAuthorPostsREST)
from resources.rating import RatingPostREST, RatingPostsREST, RatingViewREST
from config import config


DB_URI = f'postgresql+psycopg2://{config.POSTGRES_USER}:{config.POSTGRES_PW}@{config.POSTGRES_URL}/{config.POSTGRES_DB}'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = config.SECRET_KEY
db.init_app(app)


api = Api(app)


api.add_resource(UserREST, '/users')
api.add_resource(UserExitREST, '/users/logout')
api.add_resource(UserRegisterREST, '/users/register')
api.add_resource(UserAuthorizationREST, '/users/authorize')
api.add_resource(UserTokenAuthorizeREST, '/users/refresh_token')
api.add_resource(RegexREST, '/regex')
api.add_resource(RegexEditREST, '/regex/edit')
api.add_resource(RegexCreateREST, '/regex/create')
api.add_resource(RegexSearchREST, '/regex/search')
api.add_resource(RegexDeleteREST, '/regex/delete')
api.add_resource(RegexAuthorPostsREST, '/regex/author_posts')
api.add_resource(RatingPostREST, '/rating')
api.add_resource(RatingPostsREST, '/rating/posts')
api.add_resource(RatingViewREST, '/rating/view')


if __name__ == '__main__':
    app.run(debug=True)
