from flask_restful import Resource, reqparse
from sqlalchemy.sql.functions import func

from common.util import RedisDict
from models import db, Regex, Rating


r = RedisDict()


class RatingPostREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        super(RatingPostREST, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        token, regex_id = args['token'], args['regex_id']
        if token not in r:
            return {'message': {'error': 'Not authorized'}}, 401
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
        return post[0].to_dict(views=post[1], avgmark=float(post[2]))


class RatingPostsREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('limit_by', type=int, required=False, store_missing=True, default=20)
        self.reqparse.add_argument('offset', type=int, required=False, store_missing=True, default=0)
        super(RatingPostsREST, self).__init__()

    def get(self):
        args = self.reqparse.parse_args()
        token, limit_by, offset = args['token'], args['limit_by'], args['offset']
        if token not in r:
            return {'message': {'error': 'Not authorized'}}, 401
        posts = Regex.query.outerjoin(
            Rating, Regex.id == Rating.regex_id
        ).add_columns(
            func.count(Rating.regex_id).label('views'), func.avg(func.coalesce(Rating.mark, 0)).label('avgmark')
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Rating.regex_id).desc(), func.avg(func.coalesce(Rating.mark, 0)).desc()
        ).limit(limit_by).offset(0 + limit_by * offset).all()

        return [post.to_dict(views=views, avgmark=float(avgmark)) for post, views, avgmark in posts]


class RatingViewREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        self.reqparse.add_argument('mark', required=False, store_missing=True, default=0)
        super(RatingViewREST, self).__init__()

    def put(self):
        args = self.reqparse.parse_args()
        token, regex_id, mark = args['token'], args['regex_id'], args['mark']
        if token not in r:
            return {'message': {'error': 'Not authorized'}}, 401
        user_id = r[token]
        post = Rating.query.filter(Rating.regex_id == regex_id, Rating.user_id == user_id).first()
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
