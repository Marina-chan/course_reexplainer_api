import re
from os import urandom
from binascii import hexlify
from hashlib import sha512

from flask_restful import Resource, marshal_with, fields, reqparse

from models import db, User
from common.util import RedisDict


r = RedisDict()
mail_validator = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

retrieve_user = reqparse.RequestParser()
retrieve_user.add_argument('username', required=True)


class UserREST(Resource):

    def post(self):
        args = retrieve_user.parse_args()
        if len(args['username']) > 60:
            return {'error': 'invalid_username'}, 400
        user = User.query.filter_by(username=args['username']).first()
        if user:
            return {'user': user.username, 'mail': user.email}, 200
        return {'error': 'no_user'}, 400


register_user = reqparse.RequestParser()
register_user.add_argument('username', required=True)
register_user.add_argument('user_mail', required=True)
register_user.add_argument('pwd_hash', required=True)


class UserRegisterREST(Resource):

    def put(self):
        args = register_user.parse_args()
        username, user_mail, pwd_hash = args['username'], args['user_mail'], args['pwd_hash']
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
        return {'status': 'created'}, 201


authorize_user = reqparse.RequestParser()
authorize_user.add_argument('username', required=True)
authorize_user.add_argument('pwd_hash', required=True)
authorize_user.add_argument('salt', required=True)


class UserAuthorizationREST(Resource):

    def post(self):
        args = authorize_user.parse_args()
        username, pwd_hash, salt = args['username'], args['pwd_hash'], args['salt']
        if len(username) > 60:
            return {'error': 'no_user'}, 400
        user = User.query.filter_by(username=username).first()
        if not user:
            return {'error': 'no_user'}, 400
        pwd = sha512(f'{user.password}:{salt}'.encode()).hexdigest()
        if pwd == pwd_hash:
            token = sha512(f'{user.username}:{hexlify(urandom(16)).decode()}'.encode()).hexdigest()
            r[token] = user.username
            r.expire(token, 259200)
            return {'token': token}, 200


refresh_token = reqparse.RequestParser()
refresh_token.add_argument('token', required=True)


class UserTokenAuthorizeREST(Resource):

    def post(self):
        args = refresh_token.parse_args()
        if args['token'] in r:
            username = r[args['token']]
            token = sha512(f'{username}:{hexlify(urandom(16)).decode()}'.encode()).hexdigest()
            r[token] = username
            r.expire(token, 259200)
            return {'token': token}, 200
        return {'error': 'is_not_authorized'}, 408
