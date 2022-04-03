import os
import logging
import settings
import tornado.log
import tornado.web
import tornado.ioloop

from src.cache import RedisCache
from src.handlers import ProxyHandler

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def setup_logging():
    logger = logging.getLogger()
    log_file = os.environ['LOG_FILE']
    formatter = tornado.log.LogFormatter(color=False, datefmt=None)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    """
    for log in ('access', 'application', 'general'):
        logger = logging.getLogger('tornado.{}'.format(log))
        logger.addHandler(file_handler)
    """


def main():
    setup_logging()
    log.info('Starting Redis Proxy........')
    _ = RedisCache(redis_server=settings.REDIS_SERVER_IP,
                   redis_port=settings.REDIS_SERVER_PORT,
                   capacity=settings.CACHE_CAPACITY,
                   expiry_seconds=settings.CACHE_EXPIRY)

    app = tornado.web.Application([
        (r'/(.*)', ProxyHandler)
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.bind(port=int(os.environ['PROXY_PORT']),
                     address=os.environ['PROXY_IP'],
                     reuse_port=True)
    http_server.start()
    log.info('Started HTTP Server')
    tornado.ioloop.IOLoop.current().start()


if '__main__' == __name__:
    main()
