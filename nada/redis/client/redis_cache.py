import logging

from dogpile.cache import make_region

from nada.settings import settings


logger = logging.getLogger(__name__)

REDIS_CACHE_URL = settings.REDIS_CACHE_HOST
REDIS_CACHE_PORT = settings.REDIS_CACHE_PORT
REDIS_CACHE_DBNUM = settings.REDIS_CACHE_DBNUM


def single_key_generator(namespace, fn, **kw):
    """
    A simple key generator for provider model
    listings or other unique identifiers.
    Caching and selection of cache regions,
    and expiry is implemented in the provider extension.
    Simply takes the first arg.

    """
    fname = fn.__name__
    def generate_key(*arg):
        return namespace + '_' + fname + "_" + arg[0]
    return generate_key


short_region = make_region().configure(
    'dogpile.cache.redis',
    arguments = {
        'host': REDIS_CACHE_URL,
        'port': REDIS_CACHE_PORT,
        'db': REDIS_CACHE_DBNUM,
        'redis_expiration_time': 6,   # 6 seconds
        'distributed_lock': True,
        'thread_local_lock': False
        }
)

mid_region = make_region().configure(
    'dogpile.cache.redis',
    arguments = {
        'host': REDIS_CACHE_URL,
        'port': REDIS_CACHE_PORT,
        'db': REDIS_CACHE_DBNUM,
        'redis_expiration_time': 30,   # 30 seconds
        'distributed_lock': True,
        'thread_local_lock': False
        }
)

long_region = make_region().configure(
    'dogpile.cache.redis',
    arguments = {
        'host': REDIS_CACHE_URL,
        'port': REDIS_CACHE_PORT,
        'db': REDIS_CACHE_DBNUM,
        'redis_expiration_time': 300,   # 5 minutes
        'distributed_lock': True,
        'thread_local_lock': False
        }
)
