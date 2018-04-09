import re
from hashlib import sha512
from secrets import token_urlsafe

from flask_restful import Resource, reqparse

from models import db, User
from common.util import RedisDict


r = RedisDict()
mail_validator = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


class UserREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('id', type=int, required=True)

    def get(self):
        args = self.reqparse.parse_args()
        token, user_id = args['token'], args['id']
        if token not in r:
            return {'error': 'is_not_authorized'}, 408
        if not user_id:
            return {'error': 'no_user_id'}, 404
        user = User.query.filter_by(id=user_id).first()
        if user:
            return {'user': user.username}, 200
        return {'error': 'no_user'}, 404


class UserRegisterREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('username', required=True)
        self.reqparse.add_argument('user_mail', required=True)
        self.reqparse.add_argument('pwd', required=True)
        super(UserRegisterREST, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        username, user_mail, pwd_hash = args['username'], args['user_mail'], args['pwd']
        if len(username) > 60:
            return {'error': 'invalid_username'}, 400
        if len(user_mail) > 140 or not mail_validator.match(user_mail):
            return {'error': 'invalid_email'}, 400
        if User.query.filter_by(username=username).first():
            return {'error': 'user_already_exists'}, 400
        if User.query.filter_by(email=user_mail).first():
            return {'error': 'mail_already_in_use'}, 400
        user = User(username=username, email=user_mail, password=pwd_hash)
        db.session.add(user)
        db.session.commit()
        return {'user_id': User.query.filter_by(username=username).first().id}, 201


class UserAuthorizationREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('username', required=True)
        self.reqparse.add_argument('pwd', required=True)
        self.reqparse.add_argument('salt', required=True)
        super(UserAuthorizationREST, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        username, pwd_hash, salt = args['username'], args['pwd'], args['salt']
        if len(username) > 60:
            return {'error': 'no_user'}, 400
        user = User.query.filter_by(username=username).first()
        if not user:
            return {'error': 'no_user'}, 400
        pwd = sha512(f'{user.password}:{salt}'.encode()).hexdigest()
        if pwd == pwd_hash:
            token = token_urlsafe(32)
            r[token] = user.username
            r.expire(token, 259200)
            return {
                       'token': token,
                       'user_id': user.id,
                       'username': user.username
                   }, 200


class UserTokenAuthorizeREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True)
        super(UserTokenAuthorizeREST, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        if args['token'] in r:
            username = r[args['token']]
            token = token_urlsafe(32)
            r[token] = username
            r.expire(token, 259200)
            return {'token': token}, 200
        return {'error': 'is_not_authorized'}, 408
