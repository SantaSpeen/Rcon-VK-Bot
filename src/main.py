import sys
from pathlib import Path

from loguru import logger

from modules import config, rcon, get_server_status, enter_to_exit
from modules.bot import Bot
from modules.perms import Permissions

if __name__ == '__main__':
    Permissions.perm_file = Path(config.permissions_file)
    perms = Permissions.load()
    # Check token
    if not config.vk.token:
        logger.error("Токен ВК не найден.")
        enter_to_exit()
    bot = Bot()
    # Test RCON
    print("Проверка RCON..", end="")
    if rcon("list").startswith("Rcon error"):
        logger.error("RCON не отвечает. Проверьте блок \"rcon\" в config.json")
        enter_to_exit()
    logger.info("RCON доступен.")
    # Test Minecraft Server
    print("Проверка сервера..", end="")
    try:
        st = get_server_status()
        players = st.players
        logger.info(f"Сервер доступен. Пинг: {st.latency:.3f}ms, Онлайн: {players.online}/{players.max}")
    except Exception as e:
        logger.exception(e)
        logger.info("Сервер не отвечает. Проверьте блок \"minecraft\" в config.json")
        enter_to_exit()
    try:
        bot.listen()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception(e)
        enter_to_exit()
