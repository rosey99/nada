
import decimal
import json
import logging
import os
import redis
from nada.settings import settings

logger = logging.getLogger(__name__)

REDIS_DATA_HOST =  settings.REDIS_DATA_HOST
REDIS_DATA_PORT = settings.REDIS_DATA_PORT
REDIS_DATA_DBNUM = settings.REDIS_DATA_DBNUM

# TODO connection factory? and pass in a connection for these? Cache factory
#  although. . .this way it fails at startup, whcih the factory will need to do
red_con = redis.Redis(host=REDIS_DATA_HOST, port=REDIS_DATA_PORT, db=REDIS_DATA_DBNUM)

#
