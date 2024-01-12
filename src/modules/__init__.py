import json
import os
import re
import traceback
from collections import namedtuple
from datetime import datetime
from pathlib import Path

from mcrcon import MCRcon

from .perms import Permissions


def log(text, lvl=0):
    print(f"[{datetime.now()}] [{['INFO ', 'ERROR'][lvl]}] {text}")


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

if not os.path.exists("config.json"):
    log("Generating: config.json...")
    with open("config.json", "w") as f:
        f.write(raw_config)

with open('config.json') as f:
    config = json.load(f, object_hook=lambda x: namedtuple('X', x.keys())(*x.values()))

log("Starting..")
if not os.path.exists(config.vk.help_file):
    log(f"Generating: {config.vk.help_file}...")
    with open(config.vk.help_file, "w") as f:
        f.write(raw_help)

if config.minecraft.java:
    from mcstatus import JavaServer as mcs
else:
    from mcstatus import BedrockServer as mcs

host = config.rcon.host
port = config.rcon.port
password = config.rcon.password


def rcon(cmd):
    try:
        with MCRcon(host, password, port) as mcr:
            text = mcr.command(cmd)
            return re.sub(r'§.', '', text)
    except Exception as e:
        log(f"RCON ERROR with command: {cmd}", 1)
        print(traceback.format_exc())
        return f"Rcon error: {e}"


def get_server_status():
    server = mcs.lookup(config.minecraft.host, config.minecraft.port)
    return server.status()


Permissions.perm_file = Path(config.permissions_file)
perms = Permissions.load()
