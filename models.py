from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Unicode(60), unique=True, nullable=False)
    email = db.Column(db.Unicode(140), unique=True, nullable=False)
    password = db.Column(db.Unicode(128), nullable=False)

    def to_dict(self, **kwargs):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        temp.pop('password')
        temp.update(kwargs)
        return temp

    def __repr__(self):
        return f'<User {self.username}>'


class Regex(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    expression = db.Column(db.Unicode(255), nullable=False, unique=True)
    explanation = db.Column(db.Unicode(2550))
    date = db.Column(db.DateTime, default=datetime.now)
    author_id = db.Column(db.ForeignKey(User.id), nullable=False)
    author = db.relationship('User', backref=db.backref('created_posts', cascade='all,delete', lazy=True))

    def to_dict(self, **kwargs):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        temp.update({'date': self.date.strftime('%Y-%m-%d %H:%M:%S')})
        temp.update(kwargs)
        return temp

    def __repr__(self):
        return f'<Regex {self.id}:{self.author_id}>'


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    user = db.relationship('User', backref=db.backref('marked_posts', cascade='all,delete', lazy=True))
    regex_id = db.Column(db.ForeignKey(Regex.id), nullable=False)
    regex = db.relationship('Regex', backref=db.backref('marks', cascade="all,delete", lazy=True))
    mark = db.Column(db.Integer, default=db.null)

    def to_dict(self, **kwargs):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        temp.update(kwargs)
        return temp

    def __repr__(self):
        return f'<Ratings {self.id}:{self.mark}>'
