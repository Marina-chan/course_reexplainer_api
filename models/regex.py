from datetime import datetime

from models import db
from models.user import User


class Regex(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    expression = db.Column(db.Unicode(512), nullable=False, unique=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)

    def __repr__(self):
        return f'<Regex {self.id}:{self.author}>'
