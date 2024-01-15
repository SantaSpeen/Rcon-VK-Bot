import sys

from loguru import logger

from core import Bot
from modules import enter_to_exit

if __name__ == '__main__':
    bot = Bot()
    try:
        bot.listen()
    except KeyboardInterrupt:
        logger.info("Exited.")
        sys.exit(0)
    except Exception as e:
        logger.exception(e)
        enter_to_exit()
    finally:
        bot.stop()
