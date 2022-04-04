import os
import logging
import tornado.log
import tornado.web
import tornado.ioloop

from src.cache import RedisCache
from src.handlers import PingHandler, ProxyHandler, CacheHandler

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def setup_logging():
    # enable logging by adding file_handler.
    # logs will go to /redis_proxy/logs/redis_proxy.log in the container
    logger = logging.getLogger()
    log_file = os.environ['LOG_FILE']
    formatter = tornado.log.LogFormatter(color=False, datefmt=None)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)


def main():
    setup_logging()
    log.info('Starting Redis Proxy........')
    # global local cache. RedisCache is a singleton
    _ = RedisCache(redis_server=os.environ['REDIS_SERVER_IP'],
                   redis_port=int(os.environ['REDIS_SERVER_PORT']),
                   capacity=int(os.environ['CACHE_CAPACITY']),
                   expiry_seconds=float(os.environ['CACHE_EXPIRY']))

    # order of the handlers matter. r'/(.*)' should be last.
    # otherwise, it will match ping and cache
    app = tornado.web.Application([
        (r'/ping', PingHandler),
        (r'/cache', CacheHandler),
        (r'/(.*)', ProxyHandler),
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.bind(port=int(os.environ['PROXY_PORT']),
                     address=os.environ['PROXY_IP'],
                     reuse_port=True)
    http_server.start()
    log.info('Started HTTP Server')
    # asyc event-loop
    tornado.ioloop.IOLoop.current().start()


if '__main__' == __name__:
    main()
