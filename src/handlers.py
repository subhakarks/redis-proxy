import json
import logging
import settings
import tornado.escape

from src.cache import RedisCache
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, HTTPError
from concurrent.futures import ThreadPoolExecutor


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class BaseHandler(RequestHandler):
    def get_request_body(self):
        try:
            body = json.loads(self.request.body)
            return body
        except Exception as ex:
            log.error(f'{self.class_name}::> Received invalid request body: Reason: {str(ex)}')
            raise HTTPError(status_code=400, log_message=f'Invalid JSON: {str(ex)}')

    @property
    def class_name(self):
        return self.__class__.__name__


class ProxyHandler(BaseHandler):
    """
    - get() and put() methods are async functions that relinquishes control
      while waiting on I/O.
    - async def () and await are native co-routines and faster than the
      tornado's @gen.coroutine and yield() mechanisms.
    - More info at:
       - https://www.tornadoweb.org/en/stable/guide/async.html
       - https://www.tornadoweb.org/en/stable/guide/coroutines.html
    """
    executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_REQUESTS)

    def __init__(self, *args, **kwargs):
        super(ProxyHandler, self).__init__(*args, **kwargs)

    async def get(self, key, *args, **kwargs):
        # all the values in Redis are stored as bytes.
        # convert them to normal unicode strings before returning
        # them to clients
        log.info(f'Received GET Request. Key:{key}')
        cache = RedisCache.get_instance()
        ret = await IOLoop.current().run_in_executor(ProxyHandler.executor,
                                                     cache.get_item, key)
        ret['value'] = tornado.escape.to_unicode(ret['value'])
        ret.update({
            'status_code': 404 if ret['value'] is None else 200,
        })
        self.write(ret)

    async def put(self, key, *args, **kwargs):
        value = self.request.body
        # don't allow dict values as Redis doesn't support them
        # we can store them as bytes and clients can do json.loads() on them
        # but json.loads() throws exception for non-dicts. avoiding dicts for now.
        try:
            check_value = json.loads(tornado.escape.to_unicode(value))
            if isinstance(check_value, dict):
                raise HTTPError(status_code=400,
                                log_message='Invalid Data. dict value is not allowed')
        except HTTPError as ex:
            # this is ours. need to be propagated
            raise ex
        except Exception as ex:
            # this is thrown by json.loads() for non-dicts. pass it.
            _ = ex
            pass
        log.info(f'Received PUT Request. Key:{key}, Value:{value}')
        cache = RedisCache.get_instance()
        _ = await IOLoop.current().run_in_executor(ProxyHandler.executor,
                                                   cache.put_item, key, value)
        self.write({
            'key': key,
            'status_code': 200,
            'value': tornado.escape.to_unicode(value),
        })


class CacheHandler(BaseHandler):
    """
    CacheHandler is for internal testing and debugging purposes.
    - GET: will return the LRU cache capacity and current keys in local cache
    - DELETE: will clear all the entries from local cache
    """

    def get(self, *args, **kwargs):
        cache = RedisCache.get_instance()
        ret = cache.get_cache_info()
        ret.update({
            'status_code': 200
        })
        self.write(ret)

    def delete(self, *args, **kwargs):
        cache = RedisCache.get_instance()
        cache.flush_entries()
        self.write({
            'status_code': 200,
            'cache_cleared': True,
        })


class PingHandler(BaseHandler):
    """
    PingHandler can be used by clients to check if the redis-proxy
    is up and running.
    """

    def get(self, *args, **kwargs):
        self.write({
            'status_code': 200,
            'ping': 'OK'
        })
