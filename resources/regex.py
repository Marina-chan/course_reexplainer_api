from decimal import Decimal
from itertools import islice

import sqlalchemy.exc
from flask import abort
from psycopg2 import IntegrityError
from flask_restful import Resource, reqparse
from sqlalchemy.sql.functions import func

from models import db, User, Regex, Rating
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
        except (IntegrityError, sqlalchemy.exc.IntegrityError):
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
        self.reqparse.add_argument('offset', type=int, required=False, store_missing=True, default=0)
        self.reqparse.add_argument('author_id', type=int, required=True)
        super(RegexAuthorPostsREST, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        token, limit_by, offset, author_id = args['token'], args['limit_by'], args['offset'], args['author_id']
        if token not in r:
            return {'error': 'Not authorized'}, 401
        u = User.query.get_or_404(author_id)
        posts = islice(map(lambda x: x.to_dict(), u.created_posts), 0 + limit_by * offset, limit_by * offset + limit_by)
        return list(posts)


class RegexPostsREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('limit_by', required=False, store_missing=True, default=20)
        self.reqparse.add_argument('offset', type=int, required=False, store_missing=True, default=0)
        super(RegexPostsREST, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        token, limit_by, offset = args['token'], args['limit_by'], args['offset']
        if token not in r:
            return {'error': 'Not authorized'}, 401
        posts = Regex.query.outerjoin(
            Rating, Regex.id == Rating.regex_id
        ).add_columns(
            func.count(Rating.regex_id).label('views'), func.avg(func.coalesce(Rating.mark, 0)).label('avgmark')
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Rating.regex_id).desc(), func.avg(func.coalesce(Rating.mark, 0)).desc()
        ).limit(limit_by).offset(0 + limit_by * offset).all()
        p = map(lambda x: x[0].to_dict(views=x[1], avgmark=float(x[2])), posts)
        return list(p)


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
            return {'error': 'Not authorized'}, 401
        posts = Regex.query.outerjoin(
            Rating, Regex.id == Rating.regex_id
        ).add_columns(
            func.count(Rating.regex_id).label('views'), func.avg(func.coalesce(Rating.mark, 0)).label('avgmark')
        ).filter(
            Regex.expression.like(f'{regex}%')
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Regex.id).desc(), func.avg(func.coalesce(Rating.mark, 0)).desc()
        ).all()

        return [post.to_dict(views=views, avgmark=float(avgmark)) for post, views, avgmark in posts]
