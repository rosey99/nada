from typing import Union, Any

from dogpile.cache import make_region

import decimal
import json
import os
import redis

from nada.settings import settings
#logger = get_task_logger(__name__)

REDIS_CACHE_HOST = settings.REDIS_CACHE_HOST
REDIS_CACHE_PORT = settings.REDIS_CACHE_PORT
REDIS_CACHE_DBNUM = settings.REDIS_CACHE_DBNUM

REDIS_DATA_HOST =  settings.REDIS_DATA_HOST
REDIS_DATA_PORT = settings.REDIS_DATA_PORT
REDIS_DATA_DBNUM = settings.REDIS_DATA_DBNUM

# TODO connection factory? and pass in a connection for these? Cache factory
#  although. . .this way it fails at startup, which the factory will need to do
red_con = redis.Redis(host=REDIS_DATA_HOST, port=REDIS_DATA_PORT, db=REDIS_DATA_DBNUM)

#
short_region = make_region().configure(
    'dogpile.cache.redis',
    arguments = {
        'host': REDIS_CACHE_HOST,
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
        'host': REDIS_CACHE_HOST,
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
        'host': REDIS_CACHE_HOST,
        'port': REDIS_CACHE_PORT,
        'db': REDIS_CACHE_DBNUM,
        'redis_expiration_time': 300,   # 5 minutes
        'distributed_lock': True,
        'thread_local_lock': False
        }
)


def write_redis_raw(self, keys_and_vals: Union[list, dict]):
    """
    Simply sets one or more keys with no expiration. Note that in order to accomodate
    variable length results arguments via celery canvas (lists),
    and task/session binding for celery, keys and values must be passed
    wrapped in a list of dictionaries, or as a dictionary.
    """
    result = {}
    res_count = 0
    write_struct = {}
    if not keys_and_vals:
        raise ValueError('keys_and_vals must not be empty, or evaluate to False')
    if isinstance(keys_and_vals, list):
        for struct in keys_and_vals:
            if not struct or not isinstance(struct, dict):
                raise ValueError('Lists must contain non-empty dictionaries for mset')
            write_struct.update(struct)
    if isinstance(keys_and_vals, dict):
        write_struct = keys_and_vals
    if write_struct:
        res_count = red_con.mset(write_struct)
        result = { k: 1 for k in write_struct.keys() }
    return result


def get_redis_raw(keys_list):
    """
    Just for convenience, wrapper around mget, returns a dict.
    """
    if not keys_list or not isinstance(keys_list, list):
        raise ValueError('keys_list must be a non-empty sequence of strings/keys')
    res_list = red_con.mget(*keys_list)
    return dict(zip(keys_list, res_list))
