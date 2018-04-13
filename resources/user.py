import re
import sqlite3
from datetime import timedelta
from hashlib import sha512
from secrets import token_urlsafe

import sqlalchemy.exc
from flask import abort
from flask_restful import Resource, reqparse

from models import db, User
from common.util import RedisDict


r = RedisDict()
mail_validator = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


class UserREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token, which issued after authorization')
        self.reqparse.add_argument('id', type=int, required=True)
        super(UserREST, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        token, user_id = args['token'], args['id']
        if token not in r:
            return {'error': 'Not authorized'}, 401
        user = User.query.get_or_404(user_id)
        return {'user': user.username}, 200


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
        if not mail_validator.match(user_mail):
            abort(400)
        user = User(username=username, email=user_mail, password=pwd_hash)
        try:
            db.session.add(user)
            db.session.commit()
        except (sqlite3.IntegrityError, sqlalchemy.exc.IntegrityError):
            abort(404)
        return {'user_id': user.id}, 201


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
        user = User.query.filter_by(username=username).first_or_404()
        for key in r:
            if r[key] == username:
                return {'error': 'User already authorized'}, 403
        pwd = sha512(f'{user.password}:{salt}'.encode()).hexdigest()
        if pwd == pwd_hash:
            token = token_urlsafe(32)
            r[token] = user.id
            r.expire(token, timedelta(days=3).total_seconds())
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
            user_id = r[args['token']]
            token = token_urlsafe(32)
            r.pop(args['token'])
            r[token] = user_id
            r.expire(token, timedelta(days=3).total_seconds())
            return {'token': token}, 200
        return {'error': 'Not authorized'}, 401
