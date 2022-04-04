import os
import time
import unittest
from base import BaseTests


class TestProxy(BaseTests):
    def setUp(self):
        self.populate_redis_data()

    def test_cache_operation(self):
        # verify first time, key is fetched from redis
        resp = self.proxy_request(method='GET', path='9')
        self.assertEqual('redis', resp['source'])

        # verify after first time, key is fetched from local cache
        resp = self.proxy_request(method='GET', path='9')
        self.assertEqual('local', resp['source'])

        # verify after expiry time, key is fetched again from redis
        time.sleep(16)
        resp = self.proxy_request(method='GET', path='9')
        self.assertEqual('redis', resp['source'])
        print('\nVerified cache operations')

    def test_cache_capacity(self):
        # verify cache occupancy is at 0 at start-up
        resp = self.proxy_request(method='GET', path='/cache')
        self.assertEqual(0, resp['occupancy'])
        self.assertEqual(int(os.environ['CACHE_CAPACITY']), resp['capacity'])

        # verify cache occupancy is at 1 after fetching same item multiple times
        resp = self.proxy_request(method='GET', path='9')
        resp = self.proxy_request(method='GET', path='9')
        resp = self.proxy_request(method='GET', path='9')
        resp = self.proxy_request(method='GET', path='/cache')
        self.assertEqual(1, resp['occupancy'])

        # verify cache occupancy is full after fetching elements to its capacity
        resp = self.proxy_request(method='GET', path='1')
        resp = self.proxy_request(method='GET', path='2')
        resp = self.proxy_request(method='GET', path='/cache')
        self.assertEqual(3, resp['occupancy'])

        # verify cache occupancy is max-capacity even after fetching more elements than its capacity
        resp = self.proxy_request(method='GET', path='1')
        resp = self.proxy_request(method='GET', path='2')
        resp = self.proxy_request(method='GET', path='3')
        resp = self.proxy_request(method='GET', path='4')
        resp = self.proxy_request(method='GET', path='/cache')
        self.assertEqual(3, resp['occupancy'])
        print('\nVerified cache capacity')

    def test_lru_eviction(self):
        # verify local cache is full contains all 3 fetched keys
        _ = self.proxy_request(method='GET', path='1')
        _ = self.proxy_request(method='GET', path='2')
        _ = self.proxy_request(method='GET', path='3')
        resp = self.proxy_request(method='GET', path='/cache')
        time.sleep(5)
        _ = self.proxy_request(method='GET', path='1')
        _ = self.proxy_request(method='GET', path='2')
        self.assertEqual(3, resp['occupancy'])
        self.assertEqual(set(['1', '2', '3']), set(resp['keys']))
        self.assertEqual(int(os.environ['CACHE_CAPACITY']), resp['capacity'])

        # verify LRU 3 is evicted when a new key is fetched with cache being full
        _ = self.proxy_request(method='GET', path='1')
        _ = self.proxy_request(method='GET', path='2')
        _ = self.proxy_request(method='GET', path='4')
        resp = self.proxy_request(method='GET', path='/cache')
        self.assertEqual(3, resp['occupancy'])
        self.assertEqual(set(['1', '2', '4']), set(resp['keys']))
        print('\nVerified cache LRU eviction')


if __name__ == '__main__':
    unittest.main()
