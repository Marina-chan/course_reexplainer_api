import sqlite3

import sqlalchemy.exc
from flask import abort
from flask_restful import Resource, reqparse

from models import db, User, Regex
from common.util import RedisDict, ReExplain


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
            return {'error': 'Not authorized'}, 401
        re = Regex.query.get_or_404(regex_id)
        user = User.query.get_or_404(re.author_id)
        return {
            'id': re.id,
            'expression': re.expression,
            'explanation': re.explanation,
            'author': user.username
        }


class RegexChangeREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('expression', required=True)
        self.reqparse.add_argument('regex_id', type=int, required=True)
        self.reqparse.add_argument('user_id', type=int, required=True)
        super(RegexChangeREST, self).__init__()

    def put(self):
        args = self.reqparse.parse_args()
        token, regex_id, user_id, expression = args['token'], args['regex_id'], args['user_id'], args['expression']
        if token not in r:
            return {'error': 'Not authorized'}, 401
        re = Regex.query.get_or_404(regex_id)
        expr_search = Regex.query.filter_by(expression=expression).first()
        if expr_search:
            u = User.query.get_or_404(expr_search.author_id)
        else:
            u = User.query.get_or_404(user_id)
            re.expression = expression
            re.explanation = ReExplain(expression)()
            db.session.commit()
        return {
            'id': re.id,
            'expression': re.expression,
            'explanation': re.explanation,
            'author': u.username
        }, 200


class RegexDeleteREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        self.reqparse.add_argument('user_id', type=int, required=True)
        super(RegexDeleteREST, self).__init__()

    def delete(self):
        args = self.reqparse.parse_args()
        token, regex_id, author_id = args['token'], args['regex_id'], args['user_id']
        if token not in r:
            return {'error': 'Not authorized'}, 401
        re = Regex.query.get_or_404(regex_id)
        if re.author_id != author_id:
            abort(404)
        db.session.delete(re)
        db.session.commit()
        return {'status': 'ok'}, 200


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
            return {'error': 'Not authorized'}, 401
        user = User.query.get_or_404(user_id)
        explanation = ReExplain(expression)
        re = Regex(expression=expression, author_id=user.id, explanation=explanation())
        try:
            db.session.add(re)
            db.session.commit()
        except (sqlite3.IntegrityError, sqlalchemy.exc.IntegrityError):
            abort(404)
        return {
            'id': re.id,
            'expression': expression,
            'explanation': explanation()
        }, 200


class RegexAuthorPostsREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('limit_by', type=int, required=False, store_missing=True, default=20)
        self.reqparse.add_argument('offset', type=int, required=False, store_missing=True, default=1)
        self.reqparse.add_argument('author_id', type=int, required=True)
        super(RegexAuthorPostsREST, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        token, limit_by, offset, author_id = args['token'], args['limit_by'], args['offset'], args['author_id']
        u = User.query.get_or_404(author_id)
        posts = u.created_posts


class RegexPostsREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('limit_by', required=False, store_missing=True, default=20)
        self.reqparse.add_argument('offset', type=int, required=False, store_missing=True, default=1)
        super(RegexPostsREST, self).__init__()

    def get(self):
        pass


class RegexSearchREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('regex', required=True)
        super(RegexSearchREST, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        token, regex = args['token'], args['regex']
        if token not in r:
            abort(404)
        posts = Regex.query.filter(Regex.expression.like(f'{regex}%')).all()

        return [post.to_dict() for post in posts]
