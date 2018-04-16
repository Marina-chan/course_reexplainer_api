from flask import abort
from flask_restful import Resource, reqparse

from common.util import RedisDict


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
            return {'error': 'Not authorized'}, 401
        pass


class RatingPostsREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('limit_by', type=int, required=False, store_missing=True, default=20)
        self.reqparse.add_argument('offset', type=int, required=False, store_missing=True, default=1)
        super(RatingPostsREST, self).__init__()

    def get(self):
        pass


class RatingChangeREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True, help='token,which issued after authorization')
        super(RatingChangeREST, self).__init__()

    def put(self):
        pass
