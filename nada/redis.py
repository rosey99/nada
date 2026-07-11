from typing import Union, Any

from dogpile.cache import make_region

import decimal
import json
import os
import redis

from nada.settings import settings
#logger = get_task_logger(__name__)

REDIS_CACHE_HOST = settings.REDIS_CACHE_HOST #os.getenv('REDIS_CACHE_HOST')
REDIS_CACHE_PORT = settings.REDIS_CACHE_PORT #os.getenv('REDIS_CACHE_PORT')
REDIS_CACHE_DBNUM = settings.REDIS_CACHE_DBNUM # os.getenv('REDIS_CACHE_DBNUM')

REDIS_DATA_HOST =  settings.REDIS_DATA_HOST #os.getenv('REDIS_DATA_HOST')
REDIS_DATA_PORT = settings.REDIS_DATA_PORT #os.getenv('REDIS_DATA_PORT')
REDIS_DATA_DBNUM = settings.REDIS_DATA_DBNUM #os.getenv('REDIS_DATA_DBNUM')
# PM_PRICE_CACHE_TICKERS = settings.PM_PRICE_CACHE_TICKERS
# PM_PRICE_CACHE_AVERAGE = settings.PM_PRICE_CACHE_AVERAGE
# PM_PRICE_CACHE_FXRATES = settings.PM_PRICE_CACHE_FXRATES
# PM_PRICE_CACHE_ADVERTS = settings.PM_PRICE_CACHE_ADVERTS
# PM_PRICE_CACHE_FXPRICE = settings.PM_PRICE_CACHE_FXPRICE

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


def write_redis_async(self, keys_and_vals: Union[list, dict], keys_count:int=0):
    """
    This is called by the job_dispatcher as the generic, or default redis sink.
    So parsers need to respect the signature.
    """
    # TODO with this approach it is important to keep this consistent with
    #  any changes to the result formatting for ALL parsers. No bueno?
    if not keys_and_vals:
        raise

    if keys_count:
        # this means we are in batch/price mode
        return write_redis_prices(keys_count=keys_count, payload=keys_and_vals)
    if isinstance(keys_and_vals, dict):
        is_batch = keys_and_vals.get('keys_count', False)
        if is_batch:
            # also call prices
            return write_redis_prices(keys_count=is_batch, payload=keys_and_vals['keys_and_vals'])
    return write_redis_raw(keys_and_vals)

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
        raise ValueError('keys_and_vals must not be empty, orevaluate to False')
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

def write_redis_prices(self, keys_count: int, payload: list):
    """
    Calls set_prices (lua) function with pre-parsed args.
    """

    red_result = red_con.fcall('set_prices', keys_count, *payload)
    return {'set_prices': red_result}

def get_redis_raw(keys_list):
    """
    Just for convenience, wrapper around mget, returns a dict.
    """
    if not keys_list or not isinstance(keys_list, list):
        raise ValueError('keys_list must be a non-empty sequence of strings/keys')
    res_list = red_con.mget(*keys_list)
    return dict(zip(keys_list, res_list))

def get_redis_prices(price_category: str,
                     asset: str = '',
                     base_currency: str = '',
                     hi_to_low:bool = True,
                     min_val:int = 0,
                     max_val:int = 0):
    """
    This will be the entrypoint for price zrange fetches. min and max values are
    always integers.
    """
    # if asset is present, then base_currency must be, and vice versa.
    if asset and not base_currency or base_currency and not asset:
            raise ValueError('If either asset or base_currency are supplied, then both must be present')
    if asset:
        price_key = ':'.join([price_category, asset, base_currency])
    else:
        price_key = price_category
    # no negatives allowed
    min_val = 0 if min_val <= 0 else min_val
    max_val = 0 if max_val <= 0 else max_val
    hi_to_low = 'true' if hi_to_low else 'false'
    # rely on backend defaults if min and max are not present, default is get all
    if min_val or max_val:
        more_args = (min_val, max_val)
    else:
        more_args = ()
    prices_list = red_con.fcall('get_prices', 1, price_key, hi_to_low, *more_args)
    if not prices_list:
        return {}
    prices_d = parse_get_prices(prices_list)
    return prices_d
