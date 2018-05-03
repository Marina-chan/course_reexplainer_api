import os
import sys

from sqlalchemy_utils import database_exists, create_database, drop_database

from app import app, db, DB_URI
from models import User, Regex, Rating


if __name__ == '__main__':

    if not os.path.exists('config.yaml'):
        print('Please create config.yaml from config.yaml.example')
        sys.exit(0)
    print('Database URI: ', DB_URI)
    if database_exists(DB_URI):
        drop_database(DB_URI)
    create_database(DB_URI)
    with app.app_context():
        db.create_all()
    u = User(
        username='Anonymous',
        email='anonymous',
        password='b67f71a782accc6e99740fb4d0295572d81c9a15f8e9e24174e0d1a2a1cee7435d1a99833490983eaba65c68022122bcea002e29fb8d76716e97db79741819dc'
    )
    with app.app_context():
        db.session.add(u)
        db.session.commit()
    print('Setup complete')
