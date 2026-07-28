
import logging

from typing import Dict, List
import redis

from nada.settings import settings


logger = logging.getLogger(__name__)

REDIS_DATA_HOST =  settings.REDIS_DATA_HOST
REDIS_DATA_PORT = settings.REDIS_DATA_PORT
REDIS_DATA_DBNUM = settings.REDIS_DATA_DBNUM

# TODO connection factory? and pass in a connection for these? Cache factory
#  although. . .this way it fails at startup, whcih the factory will need to do
red_con = redis.Redis(host=REDIS_DATA_HOST, port=REDIS_DATA_PORT, db=REDIS_DATA_DBNUM)


class KVBase:
    def __init__(self, redis_con: redis.Redis, service_prefix: str):
        self.redis = redis_con
        self.prefix = service_prefix
        #self.services_key = service_name

    def get_services(self) -> List[str]:
        services = self.redis.smembers(self.prefix)
        return [service.decode() for service in services]

    def delete_service(self, service_name: str):
        # first, get the keys for service
        service_keys = self.redis.smembers(f'{self.prefix}:{service_name}')
        if service_keys:
            try:
                self.redis.fcall("remove_keys", len(service_keys), *service_keys)
            except Exception as e:
                logger.error('Service removal error: ', e)

    def get_service_all(self, service_name: str) -> Dict[str, str]:
        keys = self.redis.smembers(f'{self.prefix}:{service_name}')
        kvs = dict()
        for key in keys:
            k = key.decode().rsplit(':', maxsplit=1)[1]
            v = self.redis.get(key).decode()
            kvs[k] = v
        return kvs

    def add_service_keys(self, service_name: str, keys: List[str], values: List[str]):
        key_count = len(keys)
        value_count = len(values)
        real_keys = []
        if key_count != value_count:
            raise ValueError(f'The number of keys and values must be equal: got {key_count} keys and {value_count} values.')
        if key_count == 0:
            return 0
        for i in range(key_count):
            key = f'{self.prefix}:{service_name}:{keys[i]}'
            print("key: ", key)
            real_keys.append(key)
        return self.redis.fcall('set_keys', key_count, *real_keys, *values)

    def delete_service_keys(self, service_name: str, keys: List[str]):
        key_count = len(keys)
        real_keys = []
        if key_count == 0:
            return 0
        for i in range(key_count):
            key = f'{self.prefix}:{service_name}:{keys[i]}'
            real_keys.append(key)
        return self.redis.fcall('remove_keys', key_count, *real_keys)
