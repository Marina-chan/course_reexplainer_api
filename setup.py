import os
import sys

from app import db
from models.user import User
from models.regex import Regex
from models.rating import Ratings


if __name__ == '__main__':
    if not os.path.exists('config.yaml'):
        print('Please create config.yaml from config.yaml.example')
        sys.exit(0)
    db.create_all()
    u = User(
        username='Anonymous',
        email='anonymous',
        password='b67f71a782accc6e99740fb4d0295572d81c9a15f8e9e24174e0d1a2a1cee7435d1a99833490983eaba65c68022122bcea002e29fb8d76716e97db79741819dc'
    )
    db.session.add(u)
    db.session.commit()
    print('Setup complete')
