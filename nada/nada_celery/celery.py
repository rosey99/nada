
from celery import Celery
from kombu import Queue
#from dotenv import load_dotenv
from nada.settings import settings
from nada.nada_celery import tasks

"""
A test module for celery abstraction of async
jobs, probably from a web app.

"""
import os

import logging
logger = logging.getLogger(__name__)

#load_dotenv()
from nada.settings import settings

backend_uri = settings.CELERY_RESULT_URI  #os.getenv('CELERY_RESULT_URI')
broker_uri = settings.CELERY_BROKER_URI # os.getenv('CELERY_BROKER_URI')
print("BROKER: ", broker_uri)
app = Celery('nada',
            broker= broker_uri,
            backend=  backend_uri,
            include=[
                'nada.nada_celery.tasks',
                ]
            )

# Optional configuration, see the application user guide.
# We make worker_prefetch_multiplier = 1 and task_acks_late=True
#  for guaranteed single-threaded operation where the ATOMIC/sthread_tasks queue
#  is concerned.
app.conf.update(
    result_expires=3600,
    worker_prefetch_muliplier=1,
    task_acks_late=True,
    #we allow pickle for testing only
    accept_content=('json',),
    broker_connection_retry_on_startup = True,
)

app.conf.task_default_queue = 'default'
app.conf.task_queues = (
    Queue('default',    routing_key='task.default'),
    # Queue('sthread_tasks', routing_key='sthread.default'),
    # Queue('evt_tasks', routing_key='evt.default'),
)

if __name__ == '__main__':
    app.start()
