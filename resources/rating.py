from flask import abort
from flask_restful import Resource, reqparse
from sqlalchemy.sql import desc
from sqlalchemy.sql.functions import func

from common.util import RedisDict, auth_required
from models import db, Regex, Rating


r = RedisDict()


class RatingPostREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        super(RatingPostREST, self).__init__()

    @auth_required
    def get(self):
        args = self.reqparse.parse_args()
        regex_id = args['regex_id']
        post = Regex.query.outerjoin(
            Rating, Regex.id == Rating.regex_id
        ).add_columns(
            func.count(Rating.regex_id).label('views'), func.avg(func.coalesce(Rating.mark, 0)).label('avgmark')
        ).filter(
            Regex.id == regex_id
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Rating.regex_id).desc(), func.avg(func.coalesce(Rating.mark, 0)).desc()
        ).first()
        return post[0].to_dict(views=post[1], avg_mark=float(post[2])), 200


class RatingPostsREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('limit_by', type=int, required=False, store_missing=True, default=20)
        self.reqparse.add_argument('offset', type=int, required=False, store_missing=True, default=0)
        super(RatingPostsREST, self).__init__()

    @auth_required
    def get(self):
        args = self.reqparse.parse_args()
        limit_by, offset = args['limit_by'], args['offset']
        posts = Regex.query.outerjoin(
            Rating, Regex.id == Rating.regex_id
        ).add_columns(
            func.count(Rating.regex_id).label('views'), func.avg(func.coalesce(Rating.mark, 0)).label('avgmark')
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Rating.regex_id).desc(), func.avg(func.coalesce(Rating.mark, 0)).desc()
        ).limit(limit_by).offset(0 + limit_by * offset).all()

        return [post.to_dict(views=views, avg_mark=float(avgmark)) for post, views, avgmark in posts], 200


class RatingViewREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        self.reqparse.add_argument('mark', required=False, store_missing=True, default=0)
        super(RatingViewREST, self).__init__()

    @auth_required
    def put(self):
        args = self.reqparse.parse_args()
        token, regex_id, mark = args['token'], args['regex_id'], args['mark']
        user_id = int(r[token])
        if user_id == 1:
            abort(403)
        re = Regex.query.filter(Regex.id == regex_id).first()
        post = Rating.query.filter(Rating.regex_id == regex_id, Rating.user_id == user_id).first()
        if not user_id == re.author_id:
            if post:
                if not post.mark:
                    post.mark = mark
                    db.session.add(post)
                    db.session.commit()
                    return {'message': {'status': 'Changed'}}, 200
            else:
                post = Rating(user_id=user_id, regex_id=regex_id, mark=mark)
                db.session.add(post)
                db.session.commit()
                return {'message': {'status': 'Created'}}, 200
        return {'message': {'status': 'Not modified'}}, 200


class RatingHistoryREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        self.reqparse.add_argument('token', required=True)
        super(RatingHistoryREST, self).__init__()

    @auth_required
    def get(self):
        args = self.reqparse.parse_args()
        token = args['token']
        user_id = int(r[token])
        views = func.count(Rating.regex_id).label('views')
        avgmark = func.avg(func.coalesce(Rating.mark, 0)).label('avgmark')
        posts = db.session.query(
            Regex, views, avgmark
        ).outerjoin(
            Rating, Regex.id == Rating.regex_id
        ).group_by(
            Regex.id
        ).subquery()

        user_posts = db.session.query(
            Rating.mark, posts
        ).join(
            posts, posts.c.id == Rating.regex_id
        ).filter(
            Rating.user_id == user_id
        ).order_by(
            desc(posts.c.views), desc(posts.c.avgmark)
        ).all()

        return [
            {
                'id': regex_id,
                'expression': regex_expression,
                'explanation': regex_explanation,
                'date': str(regex_date),
                'author_id': regex_author_id,
                'views': regex_views,
                'avg_mark': float(regex_avgmark),
                'user_mark': user_mark
            }
            for
            user_mark,
            regex_id,
            regex_expression,
            regex_explanation,
            regex_date,
            regex_author_id,
            regex_views,
            regex_avgmark
            in user_posts
        ], 200
