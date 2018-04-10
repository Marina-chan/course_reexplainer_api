import sqlite3

import sqlalchemy.exc
from flask import abort
from flask_restful import Resource, reqparse

from models import db, User, Regex
from common.util import RedisDict


r = RedisDict()


class RegexREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        super(RegexREST, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        token, regex_id = args['token'], args['regex_id']
        if token not in r:
            abort(404)
        re = Regex.query.get_or_404(regex_id)
        user = User.query.get_or_404(re.author_id)
        return {
            'id': re.id,
            'expression': re.expression,
            'explanation': None,
            'author': user.username
        }

    def delete(self):
        pass


class RegexCreateREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token, which issued after authorization')
        self.reqparse.add_argument('expression', required=True)
        self.reqparse.add_argument('user_id', type=int, required=True)
        super(RegexCreateREST, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        token, expression, user_id = args['token'], args['expression'], args['user_id']
        if token not in r:
            abort(404)
        user = User.query.get_or_404(user_id)
        re = Regex(expression=expression, author_id=user.id)
        try:
            db.session.add(re)
            db.session.commit()
        except (sqlite3.IntegrityError, sqlalchemy.exc.IntegrityError):
            abort(404)
        # TODO: re_explain <- write semi-normal code for generating explanation for given regex
        return {
            'id': re.id,
            'expression': expression,
            'explanation': None
        }, 200
