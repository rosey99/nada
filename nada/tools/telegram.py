import logging

import requests
from requests.exceptions import ConnectionError, ConnectTimeout

from nada.settings import settings


logger = logging.getLogger(__name__)


def send_telegram_message__sync(chat_text: str):
    """

    """
    TOKEN = settings.TELEGRAM_BOT_TOKEN
    CHAT_ID = settings.TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={chat_text}"
    try:
        result = requests.get(url).json()  # this sends the messag
        logger.info(f'Telegram message sent to {CHAT_ID} with length {len(chat_text)}')
    # TODO exceptions need dead-letter and retry, just use redis with optional redis check
    except ConnectTimeout:
        logger.warning(f'Send telegram message time out: {CHAT_ID} with length {len(chat_text)}')
    except ConnectionError:
        logger.warning(f'Send telegram message connection failed: {CHAT_ID} with length {len(chat_text)}')

    return result
