import re
import sre_constants

import requests
import redis
from bs4 import BeautifulSoup


class RedisDict:

    def __init__(self, **redis_kwargs):
        self.__db = redis.Redis(**redis_kwargs)

    def __len__(self):
        return self.__db.keys().__len__()

    def __setitem__(self, key, value):
        self.__db.set(key, value)

    def __getitem__(self, key):
        k = self.__db.get(key)
        return k.decode() if k else k

    def set(self, key, value):
        self.__db.set(key, value)

    def __contains__(self, item):
        return True if self[item] else False

    def __iter__(self):
        for key in self.__db.keys():
            yield key.decode() if key else key

    def expire(self, key, time):
        self.__db.expire(key, time)

    def pop(self, key):
        return self.__db.delete(key)


class ReExplain:

    def __init__(self, expression):
        self.expression = expression

    def __call__(self):
        try:
            re.compile(self.expression)
        except sre_constants.error:
            return False
        r = requests.get(
            'http://rick.measham.id.au/paste/explain.pl',
            params={
                'regex': self.expression
            }
        )
        b = BeautifulSoup(r.text, 'html.parser')
        lines = b.pre.text.strip().splitlines()[2:]
        lines.append('-' * 80)
        res = []
        token, explanation = '', ''
        for line in lines:
            if line == '-' * 80:
                res.append((token, explanation))
                token, explanation = '', ''
                continue
            line = line.strip()
            if len(line) >= 80 // 2:
                regex_part, explanation_part = line.split(maxsplit=1)
                token = ''.join([token, regex_part])
                explanation = ''.join([explanation, explanation_part])
            else:
                if line.count(' ') == 23:
                    regex_part, explanation_part = line.split(maxsplit=1)
                    token = ''.join([token, regex_part])
                    explanation = ''.join([explanation, explanation_part])
                else:
                    explanation = ''.join([explanation, line])
        return '\n'.join(' : '.join(pair) for pair in res if all(pair))
