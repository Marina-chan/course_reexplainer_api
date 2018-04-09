from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Unicode(60), unique=True, nullable=False)
    email = db.Column(db.Unicode(140), unique=True, nullable=False)
    password = db.Column(db.Unicode(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


class Regex(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    expression = db.Column(db.Unicode(255), nullable=False, unique=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)

    def __repr__(self):
        return f'<Regex {self.id}:{self.author}>'


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    user = db.relationship('User', backref=db.backref('rates', lazy=True))
    regex_id = db.Column(db.ForeignKey(Regex.id), nullable=False)
    mark = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Ratings {self.id}:{self.mark}>'
