
import logging

from typing import Dict, List
import redis.asyncio as redis
#import redis

from nada.settings import settings


logger = logging.getLogger(__name__)

REDIS_DATA_HOST =  settings.REDIS_DATA_HOST
REDIS_DATA_PORT = settings.REDIS_DATA_PORT
REDIS_DATA_DBNUM = settings.REDIS_DATA_DBNUM
print(REDIS_DATA_DBNUM)
# connection pool
red_con = redis.Redis(host=REDIS_DATA_HOST,
                      port=REDIS_DATA_PORT,
                      db=REDIS_DATA_DBNUM,
                      max_connections=10)


red_pool = redis.ConnectionPool(
    host=REDIS_DATA_HOST,
    port=REDIS_DATA_PORT,
    db=REDIS_DATA_DBNUM,
    max_connections=10
)


class KVBase:
    def __init__(self, redis_con: redis.Redis, service_prefix: str):
        self.redis = redis_con
        self.prefix = service_prefix
        #self.services_key = service_name

    async def get_services(self) -> List[str]:
        services = await self.redis.smembers(name=self.prefix)
        if services:
            return [service.decode() for service in services]
        return []

    async def delete_service(self, service_name: str):
        # first, get the keys for service
        service_keys = await self.redis.smembers(name=f'{self.prefix}:{service_name}')
        count = 0
        if service_keys:
            try:
                await self.redis.fcall("remove_keys", len(service_keys), *service_keys)
                count = len(service_keys)
            except Exception as e:
                logger.error('Service removal error: ', e)
        return count

    async def get_service_all(self, service_name: str) -> Dict[str, str]:
        keys = await self.redis.smembers(f'{self.prefix}:{service_name}')
        kvs = dict()
        if keys:
            for key in keys:
                k = key.decode().rsplit(':', maxsplit=1)[1]
                v = await self.redis.get(key)
                kvs[k] = v.decode()
        return kvs

    async def add_service_keys(self, service_name: str, keys: List[str], values: List[str]):
        key_count = len(keys)
        value_count = len(values)
        real_keys = []
        if key_count != value_count:
            raise ValueError(f'The number of keys and values must be equal: got {key_count} keys and {value_count} values.')
        if key_count == 0:
            return 0
        for i in range(key_count):
            key = f'{self.prefix}:{service_name}:{keys[i]}'
            real_keys.append(key)
        return await self.redis.fcall('set_keys', key_count, *real_keys, *values)

    async def delete_service_keys(self, service_name: str, keys: List[str]):
        key_count = len(keys)
        real_keys = []
        if key_count == 0:
            return 0
        for i in range(key_count):
            key = f'{self.prefix}:{service_name}:{keys[i]}'
            real_keys.append(key)
        return await self.redis.fcall('remove_keys', key_count, *real_keys)

class KVContext(KVBase):
    def __init__(self, redis_con: redis.Redis, username: str):
        self.prefix=f'context_{username}'
        self.redis = red_con
        logger.info(f'Initializing kv context for user: {self.prefix}')
