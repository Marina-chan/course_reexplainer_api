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

urls = (
    (UserREST, '/users'),
    (UserExitREST, '/users/logout'),
    (UserRegisterREST, '/users/register'),
    (UserAuthorizationREST, '/users/authorize'),
    (UserTokenAuthorizeREST, '/users/refresh_token'),

    (RegexREST, '/regex'),
    (RegexEditREST, '/regex/edit'),
    (RegexCreateREST, '/regex/create'),
    (RegexSearchREST, '/regex/search'),
    (RegexDeleteREST, '/regex/delete'),
    (RegexAuthorPostsREST, '/regex/author_posts'),

    (RatingPostREST, '/rating'),
    (RatingPostsREST, '/rating/posts'),
    (RatingViewREST, '/rating/view'),
)

for url in urls:
    api.add_resource(*url)


if __name__ == '__main__':
    app.run(debug=True)
