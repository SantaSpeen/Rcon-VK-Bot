import sys
from pathlib import Path

import requests
import vk
from easydict import EasyDict
from loguru import logger

import modules
from modules import config, is_new_version
from modules.perms import Permissions
from .hosts import Hosts


class Bot:

    def __init__(self):
        self.hosts: Hosts
        self.perms: Permissions
        self._test()
        self.vk = vk.API(access_token=config["vk_token"], v=5.199)
        print("Получение GroupID..", end="")
        self.group_id = self.vk.groups.getById()['groups'][0]['id']
        with open(config["help_file"], encoding="utf-8") as f:
            self.help_message = f.read()
        logger.info(f"[BOT] ID группы: {self.group_id}")

    def _test(self):
        Permissions.perms_file = Path(config["perms_file"])
        self.perms = Permissions.load()
        self.hosts = Hosts.load()
        # Check token
        if not config["vk_token"]:
            logger.error("Токен ВК не найден.")
            modules.enter_to_exit()

    def get_lp_server(self):
        lp = self.vk.groups.getLongPollServer(group_id=self.group_id)
        return lp.get('server'), lp.get('key'), lp.get('ts')

    def write(self, peer_id, message):
        if len(message) > 4095:
            messages = (len(message) // 4095)
            for i in range(1, messages + 1):
                if i > 30:
                    logger.error("[BOT] Сообщение слишком длинное...")
                    return
                self.write(peer_id, message[:4095 * i])
        else:
            self.vk.messages.send(message=message, peer_id=peer_id, random_id=0)

    def _handle_bot(self, message, **_):
        cmds = ("Доступные команды:\n"
                "  .bot help - Вывести это сообщение.\n"
                "  .bot info - Выводит краткую информацию о боте.\n"
                "  .bot hosts list - Список доступных хостов\n"
                "  .bot hosts reload -  Перезагружает hosts.yml\n"
                # "  .bot perms user [add | del] <group> - (WIP) \n"
                # "  .bot perms list - (WIP) Выводит список групп \n"
                "  .bot perms reload - Перезагружает permissions.yml")
        tsplit = message.text.split(" ")
        if len(tsplit) == 1:
            if not message.has_perm("bot.help"): return
            message.reply(cmds)
            return
        match tsplit[1]:
            case "hosts":
                if not message.has_perm(["bot.hosts", "bot.hosts.*", "bot.hosts.reload", "bot.hosts.list"]): return
                match tsplit[2] if len(tsplit) > 2 else None:
                    case "list":
                        if not message.has_perm(["bot.hosts.*", "bot.hosts.list"]): return
                        s = ""
                        for host in self.hosts.hosts:
                            ping = 0
                            r, e = self.hosts.mine(host, True)
                            if not e:
                                ping = r.latency
                            _, e = self.hosts.rcon("list", host, True)
                            meta = self.hosts._hosts_meta[host]
                            name = meta.get("name")
                            rcon_ok = meta.get('rcon_ok')
                            mine_ok = meta.get('mine_ok')
                            if (not rcon_ok and meta['rcon'] > 0) or (not mine_ok and meta['online'] > 0):
                                s += f"\nㅤ⛔ {host} ({name})"
                            else:
                                s += f"\nㅤ✅ {host} ({name})"
                            if "-a" in tsplit or "--all" in tsplit:
                                # noinspection SpellCheckingInspection
                                s += (f":\n"
                                      f"ㅤㅤimportant: {meta['important']}\n"
                                      f"ㅤㅤrcon_default: {meta['rcon'] == 1}\n"
                                      f"ㅤㅤmine_default: {meta['online'] == 1}\n"
                                      f"ㅤㅤrcon: {not bool(e)}\n"
                                      f"ㅤㅤping: {ping:.4f}ms\n"
                                      f"ㅤㅤrcon_ok: {rcon_ok}\n"
                                      f"ㅤㅤmine_ok: {mine_ok}")
                        message.reply("Список хостов:" + s)
                    case "reload":
                        if not message.has_perm(["bot.hosts.*", "bot.hosts.reload"]): return
                        self.hosts = Hosts.load()
                        message.reply("hosts.yml - Загружен")
                    case _:
                        message.reply(".bot hosts [list | reload]")
            case "perms":
                if not message.has_perm(["bot.perms", "bot.perms.*", "bot.perms.reload"]): return
                match tsplit[2] if len(tsplit) > 2 else None:
                    case "reload":
                        if not message.has_perm(["bot.perms.*", "bot.perms.reload"]): return
                        self.perms = Permissions.load()
                        message.reply("permissions.yml - Загружен")
                    case _:
                        message.reply(".bot perms [reload]")
            case "info":
                if not message.has_perm(["bot.info"]): return
                message.reply(f"RconVkBot\n"
                              f"Версия бота: {modules.__version__}, последняя: {not is_new_version}")
            case _:
                if not message.has_perm(["bot.help"]): return
                message.reply(cmds)

    def _handle_rcon(self, message, role, host, text, _write=True):
        """Проверка прав и выполнение RCON команды"""
        if len(text) == 0: return
        cmd = text.split(" ")[0]
        if not message.has_perm(["bot.rcon.*.*", f"bot.rcon.*.{cmd}", f"bot.rcon.{host}.*", f"bot.rcon.{host}.{cmd}"]):
            return
        answer, _ = self.hosts.rcon(text, host)
        if not answer:
            answer = "Выполнено без ответа."
        logger.info(f"[BOT] User: {message['from_id']}({role}) in Chat: {message.peer_id} use RCON cmd: \"{text}\", "
                    f"with answer: \"{answer}\"")
        message.reply(("" if host == "default" else f"Ответ от {self.hosts.get_name(host)}:\n") + answer)

    def _handle_online(self, message, host, **_):
        server, _ = self.hosts.mine(host)
        players = server.players
        message.reply(f"На сервере сейчас {players.online}/{players.max}")

    def _perm_handler(self, message, perms: list | str, func: callable):
        from_id = message.from_id
        peer_id = message.peer_id
        message.has_perm = lambda x: self.perms.is_allowed(from_id, x)[0]
        if isinstance(perms, str):
            perms = [perms]
        host, text = self.hosts.parse_host(message['text'])
        for i, V in enumerate(perms):
            perms[i] = V.format(host=host)
        allow, role = self.perms.is_allowed(from_id, perms)
        logger.info(f"[BOT] {host}:{peer_id}:{from_id}:{self.perms.get_role(from_id, True)} {message['text']}")
        if allow:
            func(message=message, role=role, host=host, text=text)
        else:
            if self.perms.no_rights:  # Если есть текст
                message.reply(self.perms.no_rights)

    def message_handle(self, message):
        from_id = message.from_id
        peer_id = message.peer_id
        message.reply = lambda text: self.write(peer_id, text)
        sw = lambda t, x: t.startswith(x)
        match message.text:
            case i if sw(i, ".bot"):
                perms = [
                    "bot.help", "bot.info",
                    "bot.perms", "bot.perms.*", "bot.perms.reload",
                    "bot.hosts", "bot.hosts.*", "bot.hosts.reload", "bot.hosts.list"
                ]
                self._perm_handler(message, perms, self._handle_bot)
            case i if sw(i, ".rcon "):
                perms = ["bot.rcon.*", "bot.rcon.{host}"]
                self._perm_handler(message, perms, self._handle_rcon)
            case "!help":
                perms = ["bot.help"]
                self._perm_handler(message, perms, lambda **_: self.write(peer_id, self.help_message))
            case i if sw(i, "!online"):
                perms = ["bot.online.*", "bot.online.{host}"]
                self._perm_handler(message, perms, self._handle_online)
            case "!id":
                def __id(**_):
                    self.write(peer_id, ""
                                        f"Твой ID: {from_id}\n"
                                        f"Роль: {self.perms.get_role(from_id)}\n"
                                        f"Ник: {self.perms.get_nick(from_id)}")

                self._perm_handler(message, "bot.id", __id)

    def listen(self):
        server, key, ts = self.get_lp_server()
        session = requests.Session()
        logger.info("[BOT] Начинаю получать сообщения..")
        logger.info("[BOT] {host}:{chat_id}:{user_id}:{role} {text}")
        while True:
            lp = session.get(f'{server}?act=a_check&key={key}&ts={ts}&wait=3').json()
            try:
                if lp.get('failed') is not None:
                    key = self.get_lp_server()[1]
                if ts != lp.get('ts') and lp.get('updates'):
                    updates = lp['updates'][0]
                    if updates['type'] == "message_new":
                        # noinspection PyTypeChecker
                        self.message_handle(EasyDict(**updates['object']['message']))
                ts = lp.get('ts')
            except Exception as i:
                ts = lp.get('ts')
                logger.exception(i)

    def stop(self, signum=-1, frame=None):
        logger.debug(f"{signum=} {frame=}")
        if signum == -1:
            logger.info("Выход.")
            self.hosts.unload()
        sys.exit(0)
