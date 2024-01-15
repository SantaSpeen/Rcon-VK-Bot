import glob
import os
import sys
import zipfile
from datetime import datetime

import requests
from loguru import logger
from ruamel.yaml import YAML

yaml = YAML()
yaml.default_flow_style = False
IN_DOCKER = "DOCKER_CONTAINER" in os.environ

__version__ = '1.3.1'

raw_config_main = """\
vk_token: ""
help_file: config/help_message.txt
perms_file: config/permissions.yml
hosts_file: config/hosts.yml
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
    allow:  # Какие команды разрешены, "*" - все
      - '*'
  helper:
    name: Хелпер
    ids:
      - 583018016
    allow:
      - bot.rcon.*  # См. host.yml
      - say
      - mute
      - warn
  default:
    name: Игрок
    allow:
      - bot.online.*  # См. host.yml
      - bot.history.*  # См. host.yml

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
      rcon: 2  # RCON будет доступен по команде .rcon lobby <cmd> (разрешение: bot.rcon.lobby)
      online: 2  # !online будет доступен по команде !online lobby (разрешение: bot.online.lobby)
      history: 2  # !history будет доступен по команде !history lobby (разрешение: bot.history.lobby)
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
      history: 2
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
      history: 0
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
      history: 1
    rcon: null
    mine:
      host: 192.168.0.31
      port: 15009
"""

raw_help = """\
Тебе не нужна помощь, ты и так беспомощный, кожаный ублюдок. Так уж и быть, подскажу пару команд...
!help - Вывести это сообщение.
!online - Показать текущий онлайн на сервере.
Бот сделан кожанным петухом - админом, все вопросы к нему, я не причём.
"""

config_dir = "./config/"
config_file_main = config_dir + "bot.yml"
if not os.path.exists(config_dir):
    os.makedirs(config_dir)


def init_logger():
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
    logger.add(log_file)
    logger.add(sys.stdout, format="\r<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                                  "<level>{level: <8}</level> | {message}")


init_logger()
if not os.path.exists(config_file_main):
    logger.info(f"Создание: {config_file_main}...")
    c = yaml.load(raw_config_main)
    with open(config_file_main, "w") as f:
        yaml.dump(c, f)

with open(config_file_main) as f:
    config = yaml.load(f)

logger.info("Запуск..")
if not os.path.exists(config["help_file"]):
    logger.info(f"Создание: {config["help_file"]}...")
    with open(config.vk.help_file, "w", encoding="utf-8") as f:
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
        if ver and ver != __version__:
            logger.info("Обнаружена новая версия: {} -> {}", __version__, ver)
            return True
    except Exception as e:
        logger.error(f"Не получилось проверить обновления: {e}")
    else:
        logger.info("У вас актуальная версия")
        return False


is_new_version = new_version()
