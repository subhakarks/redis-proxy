import unittest
from base import BaseTests, REDIS_DB_SIZE


class TestConnections(BaseTests):
    def test_redis_ping(self):
        self.assertEqual(True, self.redis.ping())
        print('\nVerified connection to Redis')

    def test_proxy_ping(self):
        resp = self.proxy_request(method='GET', path='/ping')
        self.assertEqual(200, resp['status_code'])
        print('\nVerified connection to proxy')

    def test_redis_data(self):
        self.populate_redis_data()
        self.assertEqual(REDIS_DB_SIZE, self.redis.dbsize())
        print('\nVerified Redis data population')


if __name__ == '__main__':
    unittest.main()
