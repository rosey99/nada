# coding=utf-8
"""

"""
import os

from celery import shared_task  #, Task
#from celery import schedules

#from sqlalchemy_celery_beat.schedulers import DatabaseScheduler  # noqa
#from sqlalchemy_celery_beat.clockedschedule import clocked

#from nada.nada_celery import celery
#from nada.redis import short_region, mid_region, long_region


@shared_task
def add(x, y):
    return x + y


@shared_task
def echo(data):
    print(data)

@shared_task #(bind=True)
def get_ssh_keys() -> list:
    """
    checks for filesystem (readonly access)
    """
    result = os.listdir("/nada/.ssh")
    return result
