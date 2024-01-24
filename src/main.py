from loguru import logger

from core import get_bot, enter_to_exit

if __name__ == '__main__':
    bot = get_bot()
    try:
        bot.listen()
    except Exception as e:
        logger.exception(e)
        enter_to_exit()
    finally:
        bot.stop()
