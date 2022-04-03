import time
import logging
from redis import Redis
from tornado.web import HTTPError
from collections import OrderedDict
from src.singleton import SingletonMixin

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def current_timestamp():
    return float(time.time())


class CacheItem(object):

    def __init__(self, value, expiry_seconds):
        self.value = value
        self.expiry_timestamp = current_timestamp() + expiry_seconds

    def get_value(self):
        return self.value

    def has_expired(self):
        return current_timestamp() >= self.expiry_timestamp


class RedisCache(SingletonMixin):
    def __init__(self, redis_server, redis_port,
                 capacity, expiry_seconds,
                 *args, **kwargs):
        _, _ = args, kwargs
        self.redis = Redis(host=redis_server, port=redis_port)
        self.capacity = capacity
        self.lru_que = OrderedDict()
        self.expiry = expiry_seconds
        try:
            if self.redis.ping() is True:
                log.info('RC::> Established connection to Redis backend')
            else:
                log.info('RC::> Failed to connect with Redis backend')
        except Exception as ex:
            log.error(f'RC::> Error connecting to Redis backend. Reason: {str(ex)}')

    def get_item(self, key):
        try:
            item = self.lru_que[key]
            if item.has_expired():
                del self.lru_que[key]
                log.info(f'RC::> Local cache expired. Key: {key}')
                raise Exception('Item Expired')
            self.lru_que.move_to_end(key)
            log.info(f'RC::> Fetched value from local cache. Key: {key}')
            return item.get_value()
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
                return ''
            self._update_local_cache(key, value)
            log.info(f'RC::> Fetched value from Redis. Key: {key}')
            return value

    def put_item(self, key, value):
        # first store it in the redis database
        try:
            self.redis.set(key, value)
        except Exception as ex:
            lmsg = f'SET failed on Redis. Key: {key}'
            log.error(f'RC::> {lmsg}. Reason: {str(ex)}')
            raise HTTPError(status_code=500, log_message=lmsg)
        # next cache the key and value locally
        self._update_local_cache(key, value)
        log.info(f'RC::> Stored Key: {key}, Value: {value}')
        return key

    def _update_local_cache(self, key, value):
        self.lru_que[key] = CacheItem(value, self.expiry)
        self.lru_que.move_to_end(key)
        if len(self.lru_que) > self.capacity:
            (k, _) = self.lru_que.popitem(last=False)
            log.info(f'RC::> Evicted LRU item. Key: {k}')
