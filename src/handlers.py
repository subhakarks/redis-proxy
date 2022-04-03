import json
import logging
import settings

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
    executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_REQUESTS)
    # https://www.tornadoweb.org/en/stable/guide/coroutines.html

    def __init__(self, *args, **kwargs):
        super(ProxyHandler, self).__init__(*args, **kwargs)

    async def get(self, key, *args, **kwargs):
        log.info(f'Received GET Request. Key:{key}')
        cache = RedisCache.get_instance()
        value = await IOLoop.current().run_in_executor(ProxyHandler.executor,
                                                       cache.get_item, key)
        self.write(value)

    async def put(self, key, *args, **kwargs):
        value = self.request.body
        log.info(f'Received PUT Request. Key:{key}, Value:{value}')
        cache = RedisCache.get_instance()
        _ = await IOLoop.current().run_in_executor(ProxyHandler.executor,
                                                   cache.put_item, key, value)
        self.write(key)
