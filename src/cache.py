import time
import logging
from redis import Redis
from threading import RLock
from tornado.web import HTTPError
from collections import OrderedDict
from src.singleton import SingletonMixin

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def current_timestamp():
    return float(time.time())


class CacheItem(object):
    """
    CacheItem is a wrapper for the value that is stored in local cache.
    - Each item stores the expiry_timestamp when its stored in local cache
    - expiry_timestamp is used to determine the validity of the item
    """

    def __init__(self, value, expiry_seconds):
        self.value = value
        self.expiry_timestamp = current_timestamp() + expiry_seconds

    def get_value(self):
        return self.value

    def has_expired(self):
        return current_timestamp() >= self.expiry_timestamp


class RedisCache(SingletonMixin):
    """
    - RedisCache implements the local cache with LRU eviction policy.
    - it maintains a connection with the backing Redis instance.
    - LRU Cache:
      - when ever an item is read or added, it will be moved to end of the queue
      - so, the LRU item will be at the front of the queue and will be evicted if required
    - put_item():
      - will first update backing Redis with the new key-value pair
      - on successful updation to Redis, it will update the local cache with key-value pair.
      - if the cache is full, it will evict the LRU item to accomodate the new key-value pair
    - get_item():
      - will first look into the local cache if the requested key is available and if has not
        expired. if so, value from the cache will be returned
      - if item in local cache has expired, it will be removed from local cache
      - if key is not available in local cache, it will fetch the key-value pair from Redis
        and will return it.
      - before returning key-value pair, local cache will be updated with the key-value pair.
      - if the key is not available in Redis, a None value with status-code 404 will be returned
    """

    def __init__(self, redis_server, redis_port,
                 capacity, expiry_seconds,
                 *args, **kwargs):
        _, _ = args, kwargs
        self.lock = RLock()
        self.capacity = capacity
        self.lru_que = OrderedDict()
        self.expiry = expiry_seconds
        self.redis = Redis(host=redis_server, port=redis_port)
        try:
            if self.redis.ping() is True:
                log.info('RC::> Established connection to Redis backend')
            else:
                log.info('RC::> Failed to connect with Redis backend')
        except Exception as ex:
            log.error(f'RC::> Error connecting to Redis backend. Reason: {str(ex)}')

    def get_item(self, key):
        try:
            with self.lock:
                item = self.lru_que[key]
                if item.has_expired():
                    del self.lru_que[key]
                    log.info(f'RC::> Local cache expired. Key: {key}')
                    raise Exception('Item Expired')
                self.lru_que.move_to_end(key)
                log.info(f'RC::> Fetched value from local cache. Key: {key}')
                return {
                    'value': item.get_value(),
                    'source': 'local'
                }
        except Exception as ex:
            # either key is not present in local cache or it has expired.
            # need to fetch it from redis-backend
            _ = ex
            try:
                value = self.redis.get(key)
            except Exception:
                lmsg = f'GET failed on Redis. Key: {key}'
                log.error(f'RC::> {lmsg}. Reason: {str(ex)}')
                raise HTTPError(status_code=500, log_message=lmsg)
            if not value:
                log.info(f'RC::> Cache miss on Redis. Key: {key}')
                return {
                    'value': None,
                    'source': 'redis'
                }
            with self.lock:
                self._update_local_cache(key, value)
            log.info(f'RC::> Fetched value from Redis. Key: {key}')
            return {
                'value': value,
                'source': 'redis'
            }

    def put_item(self, key, value):
        # first store it in the redis database
        try:
            self.redis.set(key, value)
        except Exception as ex:
            lmsg = f'SET failed on Redis. Key: {key}'
            log.error(f'RC::> {lmsg}. Reason: {str(ex)}')
            raise HTTPError(status_code=500, log_message=lmsg)
        # next cache the key and value locally
        with self.lock:
            self._update_local_cache(key, value)
        log.info(f'RC::> Stored Key: {key}, Value: {value}')
        return key

    def _update_local_cache(self, key, value):
        self.lru_que[key] = CacheItem(value, self.expiry)
        self.lru_que.move_to_end(key)
        if len(self.lru_que) > self.capacity:
            (k, _) = self.lru_que.popitem(last=False)
            log.info(f'RC::> Evicted LRU item. Key: {k}')

    def flush_entries(self):
        with self.lock:
            self.lru_que.clear()

    def get_cache_info(self):
        with self.lock:
            occupancy = len(self.lru_que)
            cached_keys = list(self.lru_que.keys())

        return {
            'keys': cached_keys,
            'occupancy': occupancy,
            'capacity': self.capacity,
        }
