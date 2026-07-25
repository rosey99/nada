import logging

import redis

from typing import Dict, List

from dogpile.cache import make_region

from nada.settings import settings

logger = logging.getLogger(__name__)

REDIS_CACHE_URL = settings.REDIS_CACHE_HOST
REDIS_CACHE_PORT = settings.REDIS_CACHE_PORT
REDIS_CACHE_DBNUM = settings.REDIS_CACHE_DBNUM

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

class KVBase:
    def __init__(self, redis_con: redis.Redis, service_name: str):
        self.redis = redis_con
        self.prefix = "kv"
        self.services_key = service_name

    def get_services(self) -> List[str]:
        services = self.redis.smembers(self.prefix)
        return [service.decode() for service in services]

    def delete_service(self, service_name: str):
        # first, get the keys for service
        service_keys = self.redis.smembers(service_name)
        if service_keys:
            self.redis.fcall("remove_keys", len(service_keys), service_keys)

    def get_service_all(self, service_name: str) -> Dict[str, str]:
        keys = self.redis.smembers(service_name)
        kvs = dict()
        for key in keys:
            k = key.decode().rsplit(':', maxsplit=1)[0]
            v = self.redis.get(key).decode()
            kvs[k] = v
        return kvs

    def add_service_keys(self, service_name: str, keys: List[str], values: List[str]):
        key_count = len(keys)
        value_count = len(values)
        real_keys = []
        if key_count != value_count:
            raise ValueError(f'The number of keys and values must be equal: got {key_count} keys and {value_count} values.')
        for i in range(key_count):
            key = f'{self.prefix}:{service_name}:{keys[i]}'
            real_keys.append(key)
        return self.redis.fcall('set_keys', key_count, *real_keys, *values)

    def delete_service_keys(self, service_name: str, keys: List[str]):
        key_count = len(keys)
        real_keys = []
        for i in range(key_count):
            key = f'{self.prefix}:{service_name}:{keys[i]}'
            real_keys.append(key)
        return self.redis.fcall('remove_keys', key_count, *real_keys)
