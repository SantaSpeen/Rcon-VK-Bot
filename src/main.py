import platform
import signal

from loguru import logger

from core import Bot
from modules import enter_to_exit, IN_DOCKER

if __name__ == '__main__':
    bot = Bot()
    signal.signal(signal.SIGTERM, bot.stop)
    signal.signal(signal.SIGINT, bot.stop)
    if platform.system() == 'Windows':
        signal.signal(signal.SIGBREAK, bot.stop)
    elif not IN_DOCKER:
        # signal.signal(signal.SIGKILL, bot.stop)
        signal.signal(signal.SIGHUP, bot.stop)
    try:
        bot.listen()
    except Exception as e:
        logger.exception(e)
        enter_to_exit()
    finally:
        bot.stop()
