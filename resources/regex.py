from flask_restful import Resource, reqparse


class RegexREST(Resource):

    def get(self, token, id):
        pass

    def delete(self, token, id):
        pass


class RegexCreateREST(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('token', required=True)
        self.reqparse.add_argument('expression', required=True)
        self.reqparse.add_argument('user_id', type=int, required=True)

    def post(self):
        args = self.reqparse.parse_args()
        expression, user_id = args['expression'], args['user_id']
        return {
            'id': 0,
            'expression': expression,
            'explanation': None,
            'rating': 0
        }, 200
