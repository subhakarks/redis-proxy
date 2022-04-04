import unittest
from base import BaseTests


class TestProxy(BaseTests):
    def setUp(self):
        self.populate_redis_data()

    def test_get_non_existent_key(self):
        resp = self.proxy_request(method='GET', path='999')
        self.assertEqual(None, resp['value'])
        self.assertEqual(404, resp['status_code'])
        print('\nVerified GET on non-existent key')

    def test_get_valid_key(self):
        redis_val = self.redis.get(9).decode('utf-8')
        resp = self.proxy_request(method='GET', path='9')
        self.assertEqual(redis_val, resp['value'])
        self.assertEqual(200, resp['status_code'])
        print('\nVerified GET on valid existent key')
        # verify update of a key
        resp = self.proxy_request(method='PUT', path='9', data='9999')
        self.assertEqual(200, resp['status_code'])
        resp = self.proxy_request(method='GET', path='9')
        self.assertEqual('9999', resp['value'])
        self.assertEqual(200, resp['status_code'])
        print('\nVerified GET on update of existent key')


if __name__ == '__main__':
    unittest.main()
