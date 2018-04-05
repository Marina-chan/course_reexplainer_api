from models import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Unicode(60), unique=True, nullable=False)
    email = db.Column(db.Unicode(140), unique=True, nullable=False)
    password = db.Column(db.Unicode(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
