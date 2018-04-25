from flask_restful import Resource, reqparse
from sqlalchemy.sql.functions import func

from common.util import RedisDict, auth_required
from models import db, Regex, Rating


r = RedisDict()


class RatingPostREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
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
            func.avg(func.coalesce(Rating.mark, 0)).desc(), func.count(Rating.regex_id).desc()
        ).first()
        return post[0].to_dict(views=post[1], avgmark=float(post[2])), 200


class RatingPostsREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
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
            func.avg(func.coalesce(Rating.mark, 0)).desc(), func.count(Rating.regex_id).desc()
        ).limit(limit_by).offset(0 + limit_by * offset).all()

        return [post.to_dict(views=views, avgmark=float(avgmark)) for post, views, avgmark in posts], 200


class RatingViewREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        self.reqparse.add_argument('regex_id', type=int, required=True)
        self.reqparse.add_argument('mark', required=False, store_missing=True, default=0)
        super(RatingViewREST, self).__init__()

    @auth_required
    def put(self):
        args = self.reqparse.parse_args()
        token, regex_id, mark = args['token'], args['regex_id'], args['mark']
        user_id = r[token]
        post = Rating.query.filter(Rating.regex_id == regex_id, Rating.user_id == user_id).first()
        if not user_id == post.author_id:
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
