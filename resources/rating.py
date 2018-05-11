from flask import abort
from flask_restful import Resource, reqparse
from sqlalchemy.sql import desc
from sqlalchemy.sql.functions import func

from common.util import RedisDict, auth_required
from models import db, User, Regex, Rating


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
            func.count(Rating.regex_id).label('views'), func.avg(Rating.mark).label('avgmark')
        ).filter(
            Regex.id == regex_id
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Rating.regex_id).desc(), func.avg(Rating.mark).desc()
        ).first()
        post, views, avg_mark = post[0], post[1], post[2]
        user = User.query.get_or_404(post.author_id)
        return post.to_dict(author=user.username, views=views, avg_mark=float(avg_mark) if avg_mark else 0), 200


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
            func.count(Rating.regex_id).label('views'), func.avg(Rating.mark).label('avgmark')
        ).group_by(
            Regex.id
        ).order_by(
            func.count(Rating.regex_id).desc(), func.avg(Rating.mark).desc()
        ).all()  # .limit(limit_by).offset(0 + limit_by * offset)

        return [post.to_dict(views=views, avg_mark=float(avgmark)) if avgmark else post.to_dict(views=views, avg_mark=0) for post, views, avgmark in posts], 200


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
                if mark:
                    post = Rating(user_id=user_id, regex_id=regex_id, mark=mark)
                else:
                    post = Rating(user_id=user_id, regex_id=regex_id)
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
        avgmark = func.avg(Rating.mark).label('avgmark')
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
                'views': regex_views,
                'avg_mark': float(regex_avgmark) if regex_avgmark else 0,
                'user_mark': user_mark
            }
            for
            user_mark,
            regex_id,
            regex_expression,
            regex_explanation,
            regex_date,
            _,
            regex_views,
            regex_avgmark
            in user_posts
        ], 200
