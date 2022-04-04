import os
import string
import random
import requests
import unittest
from redis import Redis

REDIS_DB_SIZE = 15
REDIS_VALUE_SIZE = 16


class BaseTests(unittest.TestCase):

    def populate_redis_data(self):
        """
        - Clears redis-proxy cache
        - Clears redis database
        - Populates redis database with keys 1-15 and random string values
        """
        self.clear_cache()
        self.redis.flushdb()
        for idx in range(1, REDIS_DB_SIZE + 1):
            val = ''.join(random.choices(string.ascii_lowercase, k=REDIS_VALUE_SIZE))
            self.redis.set(str(idx), val)
        print('\nPopulated Redis data')

    def clear_cache(self):
        resp = self.proxy_request(method='DELETE', path='/cache')
        if 200 == resp['status_code']:
            print('Cleared local cache')
        else:
            print('Failed to clear local cache')

    def proxy_request(self, method='GET', path=None, data=None):
        path = path.strip('/')
        method = method.upper()
        path = '{}/{}'.format(self.proxy_base_url, path) if path else self.proxy_base_url
        resp = requests.request(method=method,
                                url=path,
                                data=data or {})
        return resp.json()

    @property
    def proxy_base_url(self):
        if not hasattr(self, '_proxy_base_url'):
            _proxy_base_url = 'http://{}:{}'.format(os.environ['PROXY_IP'], os.environ['PROXY_PORT'])
            setattr(self, '_proxy_base_url', _proxy_base_url)
        return getattr(self, '_proxy_base_url')

    @property
    def redis(self):
        if not hasattr(self, '_redis'):
            redis = Redis(host=os.environ['REDIS_SERVER_IP'],
                          port=os.environ['REDIS_SERVER_PORT'])
            setattr(self, '_redis', redis)
        return getattr(self, '_redis')
