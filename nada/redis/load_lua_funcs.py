# A loader script that will connect and load our lua into the redis
#  defined in the environment. This should probably be run as part of deploy
#  and not at application node/worker node startup. Just sayin'
import asyncio
import os

from nada.redis.client.redis_data import red_con


def load_funcs():
    # load up the redis funcs
    # get a path
    THIS_DIR = os.path.abspath(os.path.dirname(__file__))
    lua_path = os.path.join(THIS_DIR, 'lua/kv.lua')

    with open(lua_path, 'r') as lfile:
        this_code = lfile.read()
    res = asyncio.run(red_con.function_load(this_code, replace=True))
    return res
