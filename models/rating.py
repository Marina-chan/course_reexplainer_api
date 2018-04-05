from models import db
from models.user import User
from models.regex import Regex


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    user = db.relationship('User', backref=db.backref('rates', lazy=True))
    regex_id = db.Column(db.ForeignKey(Regex.id), nullable=False)
    mark = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Ratings {self.id}:{self.mark}>'
