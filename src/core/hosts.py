import os
import re
from pathlib import Path

from loguru import logger
from mcrcon import MCRcon
from mcstatus import JavaServer, BedrockServer

from modules import yaml, raw_config_hosts, enter_to_exit


class Hosts:
    hosts_config = Path("config/hosts.yml")

    def __init__(self, **kwargs):
        self._hosts = kwargs["hosts"]
        self.hosts = set()
        self._hosts_rcon = {}
        self._hosts_mine = {}
        self._hosts_meta = {}
        self._connect()
        logger.info("[HOSTS] Хосты загружены")

    def rcon(self, cmd: str, server: str = "default", update=False) -> tuple[str | None, Exception | None]:
        if not update and not self._hosts_meta[server].get('rcon_ok', True):
            return ("Сервер в листе нерабочих.\nЕсли это не так, обновить можно этой командой\n.bot hosts list",
                    Exception("Сервер в листе нерабочих"))
        if server not in self._hosts_rcon:
            return "Сервер не найден", Exception("Сервер не найден")
        try:
            with MCRcon(**self._hosts_rcon[server]) as mcr:
                text = mcr.command(cmd)
            self._hosts_meta[server]['rcon_ok'] = True
            return re.sub(r'§.', '', text), None
        except Exception as e:
            self._hosts_meta[server]['rcon_ok'] = False
            logger.error(f"[RCON] Сервер: {server}; Команда: {cmd}")
            logger.error(e)
            return f"error: \"{e}\"", e

    def mine(self, server: str = "default", update=False) -> tuple[JavaServer.lookup, Exception | None]:
        if not update and not self._hosts_meta[server].get('mine_ok', True):
            return ("Сервер в листе нерабочих.\nЕсли это не так, обновить можно этой командой\n.bot hosts list",
                    Exception("Сервер в листе нерабочих"))
        if server not in self._hosts_mine:
            return None, Exception("Сервер не найден")
        s = self._hosts_mine[server]
        try:
            if self._hosts_meta[server]["java"]:
                srv = JavaServer.lookup(f'{s["host"]}:{s["port"]}').status()
            else:
                # noinspection PyArgumentList
                srv = BedrockServer.lookup(f'{s["host"]}:{s["port"]}').status()
            self._hosts_meta[server]['mine_ok'] = True
            return srv, None
        except Exception as e:
            self._hosts_meta[server]['mine_ok'] = False
            logger.error(f"[MINE] Сервер не отвечает: {server} {s}")
            logger.exception(e)
            self._hosts_meta["connected"] = False
            return None, e

    def _connect(self) -> None:
        if self._hosts is None or len(self._hosts) == 0:
            logger.error("[HOSTS] Не найдено ни одного хоста.")
            enter_to_exit()

        self._hosts_meta['default'] = {}

        # Test RCON
        for name in self._hosts:
            self.hosts.add(name)
            server = self._hosts[name]
            meta = self._hosts_meta[name] = server['meta']
            if meta['rcon'] > 0:
                rcon = self._hosts_rcon[name] = server['rcon']
                print(f"Проверка RCON {name}..", end="")
                srv, e = self.rcon("list", name)
                if srv:
                    if meta['rcon'] == 1:
                        if self._hosts_rcon.get('default'):
                            logger.warning(f"[RCON] hosts.{name}.meta.rcon = 1 - Хотя уже есть дефолтный.")
                        self._hosts_rcon['default'] = rcon
                        self._hosts_meta['default']['rcon_ok'] = True
                    logger.info(f"[RCON] {name} доступен.")
                else:
                    if meta["important"]:
                        logger.error(f"[RCON] Важный хост не доступен: {name}")
                        enter_to_exit()
            if meta["online"] > 0:
                mine = self._hosts_mine[name] = server['mine']
                print(f"Проверка MINE {name}..", end="")
                srv, e = self.mine(name)
                if srv:
                    if meta['online'] == 1:
                        if self._hosts_mine.get('default'):
                            logger.warning(f"[RCON] hosts.{name}.meta.online = 1 - Хотя уже есть дефолтный.")
                        self._hosts_mine['default'] = mine
                        self._hosts_meta['default']['java'] = meta['java']
                        self._hosts_meta['default']['mine_ok'] = True
                    players = srv.players
                    logger.info(f"[MINE] {name} доступен. {players.online}/{players.max} {srv.latency:.3f}ms")
                else:
                    if meta["important"]:
                        logger.error(f"[MINE] Важный хост не доступен: {name}")
                        enter_to_exit()

    @classmethod
    def load(cls) -> "Hosts":
        if os.path.exists(cls.hosts_config):
            data = yaml.load(cls.hosts_config)
            if not data:
                os.remove(cls.hosts_config)
                return cls.load()
        else:
            data = yaml.load(raw_config_hosts)
            with open(cls.hosts_config, mode="w", encoding="utf-8") as f:
                yaml.dump(data, f)

        logger.info(f"[HOSTS] {cls.hosts_config} - загружен")
        return Hosts(**data)

    def unload(self):
        return
