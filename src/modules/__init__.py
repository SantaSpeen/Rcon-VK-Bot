import glob
import json
import os
import re
import sys
import zipfile
from collections import namedtuple
from datetime import datetime

import requests
from loguru import logger
from mcrcon import MCRcon
from ruamel.yaml import YAML

yaml = YAML()
yaml.default_flow_style = False
IN_DOCKER = "DOCKER_CONTAINER" in os.environ

__version__ = '1.3.1'

raw_config = """\
{
  "vk": {
    "token": "",
    "help_file": "help_message.txt"
  },
  "rcon": {
    "host": "127.0.0.1",
    "port": 25575,
    "password": "P@ssw0rd"
  },
  "minecraft": {
    "host": "127.0.0.1",
    "port": 25565,
    "java": true
  },
  "permissions_file": "permissions.yml"
}"""

raw_help = """\
Тебе не нужна помощь, ты и так беспомощный, кожаный ублюдок. Так уж и быть, подскажу пару команд...
!help - Вывести это сообщение.
!online - Показать текущий онлайн на сервере.
Бот сделан кожанным петухом - админом, все вопросы к нему, я не причём.
"""


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
if not os.path.exists("config.json"):
    logger.info("Создание: config.json...")
    with open("config.json", "w") as f:
        f.write(raw_config)

with open('config.json') as f:
    config = json.load(f, object_hook=lambda x: namedtuple('X', x.keys())(*x.values()))

logger.info("Запуск..")
if not os.path.exists(config.vk.help_file):
    logger.info(f"Создание: {config.vk.help_file}...")
    with open(config.vk.help_file, "w", encoding="utf-8") as f:
        f.write(raw_help)

if config.minecraft.java:
    from mcstatus import JavaServer as MineServer
else:
    from mcstatus import BedrockServer as MineServer

host = config.rcon.host
port = config.rcon.port
password = config.rcon.password


def rcon(cmd):
    try:
        with MCRcon(host, password, port) as mcr:
            text = mcr.command(cmd)
            return re.sub(r'§.', '', text)
    except Exception as e:
        logger.error(f"[RCON] ERROR with command: {cmd}")
        logger.exception(e)
        return f"Rcon error: {e}"


def get_server_status():
    server = MineServer.lookup(config.minecraft.host, config.minecraft.port)
    return server.status()


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
    except:
        logger.error("Не получилось проверить обновления.")
    else:
        logger.info("У вас актуальная версия")
        return False


is_new_version = new_version()
