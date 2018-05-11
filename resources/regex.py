import sqlalchemy.exc
from flask import abort
from psycopg2 import IntegrityError
from flask_restful import Resource, reqparse
from sqlalchemy.sql.functions import func

from models import db, User, Regex, Rating
from common.util import RedisDict, auth_required, get_re_explanation


r = RedisDict()


class RegexREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        super(RegexREST, self).__init__()

    @auth_required
    def get(self):
        args = self.reqparse.parse_args()
        regex_id = args['regex_id']
        re = Regex.query.get_or_404(regex_id)
        user = User.query.get_or_404(re.author_id)
        return {
            'id': re.id,
            'expression': re.expression,
            'explanation': re.explanation,
            'author': user.username
        }, 200


class RegexEditREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('expression', required=True)
        self.reqparse.add_argument('regex_id', type=int, required=True)
        super(RegexEditREST, self).__init__()

    @auth_required
    def put(self):
        args = self.reqparse.parse_args()
        token, regex_id, expression = args['token'], args['regex_id'], args['expression']
        user_id = int(r[token])
        if user_id == 1:
            abort(403)
        re = Regex.query.get_or_404(regex_id)
        expr_search = Regex.query.filter_by(expression=expression).first()
        if expr_search:
            return {'message': {'status': 'Regex already exists'}}, 303
        elif re.author_id != user_id:
            abort(403)
        else:
            u = User.query.get_or_404(user_id)
            re.expression = expression
            explanation = get_re_explanation(expression)
            if not explanation:
                abort(403)
            re.explanation = explanation
            db.session.commit()
        return {
            'id': re.id,
            'expression': re.expression,
            'explanation': re.explanation,
            'author': u.username
        }, 200


class RegexDeleteREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        self.reqparse.add_argument('user_id', type=int, required=True)
        super(RegexDeleteREST, self).__init__()

    @auth_required
    def delete(self):
        args = self.reqparse.parse_args()
        regex_id, author_id = args['regex_id'], args['user_id']
        if author_id == 1:
            abort(403)
        re = Regex.query.get_or_404(regex_id)
        if re.author_id != author_id:
            abort(404)
        db.session.delete(re)
        db.session.commit()
        return {'message': {'status': 'ok'}}, 200


class RegexCreateREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True, help='token, which issued after authorization')
        self.reqparse.add_argument('expression', required=True)
        super(RegexCreateREST, self).__init__()

    @auth_required
    def post(self):
        args = self.reqparse.parse_args()
        token, expression = args['token'], args['expression']
        user_id = int(r[token])
        user = User.query.get_or_404(user_id)
        explanation = get_re_explanation(expression)
        if not explanation:
            abort(403)
        re = Regex(expression=expression, author_id=user.id, explanation=explanation)
        try:
            db.session.add(re)
            db.session.commit()
        except (IntegrityError, sqlalchemy.exc.IntegrityError):
            abort(404)
        return {
            'id': re.id,
            'expression': re.expression,
            'explanation': re.explanation
        }, 200


class RegexAuthorPostsREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('limit_by', type=int, required=False, store_missing=True, default=20)
        self.reqparse.add_argument('offset', type=int, required=False, store_missing=True, default=0)
        self.reqparse.add_argument('author_id', type=int, required=True)
        super(RegexAuthorPostsREST, self).__init__()

    @auth_required
    def get(self):
        args = self.reqparse.parse_args()
        token, limit_by, offset, author_id = args['token'], args['limit_by'], args['offset'], args['author_id']
        if int(r[token]) != author_id:
            abort(403)
        u = User.query.get_or_404(author_id)

        posts = Regex.query.outerjoin(
            Rating, Regex.id == Rating.regex_id
        ).add_columns(
            func.count(Rating.regex_id).label('views'), func.avg(Rating.mark).label('avgmark')
        ).filter(
            Regex.author_id == u.id
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Rating.regex_id).desc(), func.avg(Rating.mark).desc()
        ).all()

        return [post.to_dict(views=views, avg_mark=float(avgmark), author=u.username) for post, views, avgmark in posts], 200


class RegexSearchREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('regex', required=True)
        super(RegexSearchREST, self).__init__()

    @auth_required
    def post(self):
        args = self.reqparse.parse_args()
        regex = args['regex']
        posts = Regex.query.outerjoin(
            Rating, Regex.id == Rating.regex_id
        ).add_columns(
            func.count(Rating.regex_id).label('views'), func.avg(Rating.mark).label('avgmark')
        ).filter(
            Regex.expression.like(f'{regex}%')
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Rating.regex_id).desc(), func.avg(Rating.mark).desc()
        ).all()

        return [post.to_dict(views=views, avg_mark=float(avgmark)) for post, views, avgmark in posts], 200
