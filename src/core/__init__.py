import glob
import os
import platform
import signal
import sys
import zipfile
from datetime import datetime

import requests
from loguru import logger
from ruamel.yaml import YAML

yaml = YAML()
yaml.default_flow_style = False
IN_DOCKER = "IN_DOCKER" in os.environ

__version__ = '2.1.0'

config_dir = "config/" if IN_DOCKER else ""

raw_config_main = f"""\
# Работа протестирована на LongPool 5.199
vk_token: ""  # Токен ВК
help_file: {config_dir}help_message.txt  # Файл, который будет выводиться на !help
perms_file: {config_dir}permissions.yml  # Конфиг с настройками разрешений для пользователей
hosts_file: {config_dir}hosts.yml  # Конфиг с настройками хостов
store_file: {config_dir}store/sql.yml  # Конфиг с настройками где хранить историю онлайна
"""

raw_config_perms = """\
noRole: Нет роли
noRights: Нет прав  # null для отключения
noNick: Не указан  # Используется для !id

# Таблица соответствия vkID к нику в Майнкрафте
# Ник будет передаваться в плагины (Плагины бота)
nicks:
  370926160: Rick
  583018016: SantaSpeen

perms:
  admin:  # Имя группы
    name: Админ  # Имя группы, которое будет отображаться в боте
    ids:  # вк ИД входящих в состав группы
    - 370926160
    parent:  # Наследование прав
    - helper
    allow:  # Права, подробнее в readme.md
    - bot.*
#    - bot.help
#    - bot.info
#    - bot.hosts
#    - bot.hosts.*
#    - bot.hosts.list
#    - bot.hosts.reload
#    - bot.perms
#    - bot.hosts.*
#    - bot.hosts.reload
#    - bot.cmd.*
#    - bot.cmd.help
#    - bot.cmd.id
#    - bot.online.*
#    - bot.online.default
#    - bot.online.lobby
#    - bot.history.*
#    - bot.history.default
#    - bot.history.lobby
#    - bot.rcon.*
#    - bot.rcon.*.*
  helper:
    name: Хелпер
    ids:
    - 583018016
    allow:
    - bot.rcon.default
    - bot.rcon.lobby
    - bot.rcon.survival
    - bot.rcon.*.say
    - bot.rcon.*.mute
    - bot.rcon.survival.ban
    - bot.rcon.survival.tempban
  default:
    name: Игрок
    allow:
    - bot.cmd.help
    - bot.cmd.id
    - bot.cmd.online.*
    - bot.cmd.history.*
"""

raw_config_hosts = """\
hosts:
  survival:  # Название сервера (имя), может быть любым, может быть сколько угодно
    meta:
      name: Выживание  # Это имя будет выводиться в ответе, или статистике (имя для бота)
      java: true  # Это JAVA сервер?
      important: true  # Если да, то бот не включится, если не подключится
      # 0 - выключен
      # 1 - Доступно без имени (!! Такое значение может быть только у 1 хоста !!) (.rcon <cmd>)
      # 2 - Доступно с именем (.rcon <name> <cmd>)
      # Разрешение: bot.rcon.<name>; bot.online.<name>; bot.history.<name>
      # При запуске бота будет проверка доступности всего
      rcon: 2  # RCON будет доступен по команде .rcon survival <cmd> (разрешение: bot.rcon.survival)
      # !online будет доступен по команде !online survival (разрешение: bot.cmd.online.survival)
      # !history будет доступен по команде !history survival (разрешение: bot.cmd.history.survival)
      online: 2
    rcon:  # RCON подключение
      host: 192.168.0.31
      port: 15101
      password: rconPass1
    mine:  # Minecraft подключение (нужно для !online и !history)
      host: 192.168.0.31
      port: 15001

  lobby:
    meta:
      name: Лобби
      important: true
      java: true
      rcon: 1
      online: 2
    rcon:
      host: 192.168.0.31
      port: 15100
      password: rconPass2
    mine:
      host: 192.168.0.31
      port: 15000

  devlobby:
    meta:
      name: Лобби
      important: false
      java: true
      rcon: 2
      online: 2
    rcon:
      host: 192.168.0.31
      port: 15108
      password: rconPass3
    mine:
      host: 192.168.0.31
      port: 15008

  proxy-local:
    meta:
      name: Proxy-Local
      java: true
      important: true
      rcon: 0
      online: 1
    rcon:
    mine:
      host: 192.168.0.31
      port: 15009
"""

raw_help = """\
!help - Вывести это сообщение
!online - Показать текущий онлайн на сервере
"""

config_file_main = config_dir + "bot.yml"
if config_dir and not os.path.exists(config_dir):
    os.makedirs(config_dir)


def init_logger():
    log_debug = "./logs/debug.log"
    log_file = "./logs/latest.log"
    log_dir = os.path.dirname(log_file) + "/"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if os.path.exists(log_file):
        ftime = os.path.getmtime(log_file)
        zip_path = log_dir + datetime.fromtimestamp(ftime).strftime('%Y-%m-%d') + "-%s.zip"
        index = 1
        while True:
            if not os.path.exists(zip_path % index):
                break
            index += 1
        with zipfile.ZipFile(zip_path % index, "w") as zipf:
            logs_files = glob.glob(f"{log_dir}/*.log")
            for file in logs_files:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))
                    os.remove(file)
    logger.remove(0)
    logger.add(log_debug, level=0, backtrace=True, diagnose=True)
    logger.add(log_file, level="INFO", backtrace=False, diagnose=False,
               format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}")
    logger.add(sys.stdout,  level="INFO", backtrace=False, diagnose=False,
               format="\r<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}")


init_logger()
if not os.path.exists(config_file_main):
    logger.info(f"Создание: {config_file_main}...")
    c = yaml.load(raw_config_main)
    with open(config_file_main, "w", encoding="utf-8") as f:
        yaml.dump(c, f)

with open(config_file_main, encoding="utf-8") as f:
    config = yaml.load(f)

logger.info("Запуск..")
if IN_DOCKER:
    logger.info("Обнаружен запуск из DOCKER")
if not os.path.exists(config["help_file"]):
    logger.info(f"Создание: {config["help_file"]}...")
    with open(config["help_file"], "w", encoding="utf-8") as f:
        f.write(raw_help)


def enter_to_exit(exit_code=1):
    logger.info("Выход..")
    if not IN_DOCKER:
        input("\nНажмите Enter для продолжения..")
    sys.exit(exit_code)


def new_version():
    print("Проверка версии...", end="")
    try:
        res = requests.get("https://raw.githubusercontent.com/SantaSpeen/Rcon-VK-Bot/master/win/metadata.yml")
        data = yaml.load(res.text)
        ver = data.get("Version")
        if ver:
            if int(ver.replace(".", "").replace("-", "")) > int(__version__.replace(".", "").replace("-", "")):
                logger.info("Обнаружена новая версия: {} -> {}", __version__, ver)
                return True
            else:
                logger.warning(f"У вас DEV версия: {__version__} (Актуальная: {ver})")
                return "DEV"
    except Exception as e:
        logger.error(f"Не получилось проверить обновления: {e}")
    else:
        logger.info("У вас актуальная версия")
        return False


is_new_version = new_version()


def get_bot():
    from .bot import Bot
    bot = Bot()
    signal.signal(signal.SIGTERM, bot.stop)
    signal.signal(signal.SIGINT, bot.stop)
    if platform.system() == 'Windows':
        signal.signal(signal.SIGBREAK, bot.stop)
    elif not IN_DOCKER:
        # signal.signal(signal.SIGKILL, bot.stop)
        signal.signal(signal.SIGHUP, bot.stop)
    return bot

