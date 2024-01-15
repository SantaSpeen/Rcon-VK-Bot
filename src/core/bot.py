from pathlib import Path

import requests
import vk
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
        Permissions.perm_file = Path(config["perms_file"])
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

    def _handle_rcon(self, message, _write=True, allow=False):
        """Проверка прав и выполнение RCON команды"""
        from_id = message['from_id']
        peer_id = message['peer_id']
        text = message['text']
        logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
        tsplit = text.split(" ")
        if allow:
            role = "console"
        else:
            if tsplit[1] in self.hosts.hosts:
                props = {"cmd": " ".join(tsplit[2:]), "server": tsplit[1]}
            else:
                props = {"cmd": " ".join(tsplit[1:])}
            allow, role = self.perms.is_allowed(from_id, props['cmd'])
        if allow:
            answer, _ = self.hosts.rcon(**props)
            if not answer:
                answer = "Выполнено без ответа."
            logger.info(f"[BOT] User: {from_id}({role}) in Chat: {peer_id} use RCON cmd: \"{props['cmd']}\", "
                        f"with answer: \"{answer}\"")
            if _write:
                self.write(peer_id, ("" if not props.get("server") else f"Ответ от {self.hosts._hosts_meta[props["server"]].get("name", props["server"])}:\n") + answer)
            else:
                return answer
        else:
            logger.info(f"[BOT] User: {from_id}({role}) in Chat: {peer_id} no have rights RCON cmd: \"{props['cmd']}\".")
            if self.perms.no_rights:  # Если есть текст
                self.write(peer_id, self.perms.no_rights)

    def _handle_bot(self, message):
        from_id = message['from_id']
        if self.perms.is_allowed(from_id, "bot"):
            peer_id = message['peer_id']
            text = message['text']
            logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
            tsplit = text.split(" ")
            cmds = ("Доступные команды:\n"
                    "  .bot help - Вывести это сообщение.\n"
                    "  .bot info - Выводит краткую информацию о боте.\n"
                    "  .bot hosts list - Список доступных хостов\n"
                    "  .bot hosts reload -  Перезагружает hosts.yml\n"
                    # "  .bot perms user [add | del] <group> - не реализовано \n"
                    # "  .bot perms list - Выводит список групп \n"
                    "  .bot perms reload - Перезагружает permissions.yml")
            if len(tsplit) == 1:
                self.write(peer_id, cmds)
                return
            match tsplit[1]:
                case "hosts":
                    match tsplit[2] if len(tsplit) > 2 else None:
                        case "list":
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
                            self.write(peer_id, "Список хостов:" + s)
                        case "reload":
                            self.hosts = Hosts.load()
                            self.write(peer_id, "hosts.yml - Загружен")
                        case _:
                            self.write(peer_id, ".bot hosts [list | reload]")
                case "perms":
                    match tsplit[2] if len(tsplit) > 2 else None:
                        case "reload":
                            self.perms = Permissions.load()
                            self.write(peer_id, "permissions.yml - Загружен")
                        case _:
                            self.write(peer_id, ".bot perms [reload]")
                case "info":
                    self.write(peer_id, f"RconVkBot\n"
                                        f"Версия бота: {modules.__version__}, последняя: {not is_new_version}")
                case _:
                    self.write(peer_id, cmds)

    def message_handle(self, message):
        from_id = message['from_id']
        peer_id = message['peer_id']
        text = message['text']
        match text:
            case i if i.startswith(".rcon "):
                self._handle_rcon(message)
            case i if i.startswith(".bot"):
                self._handle_bot(message)
            case "!help":
                logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
                self.write(peer_id, self.help_message)
            case "!online":
                logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
                server, _ = self.hosts.mine()
                players = server.players
                self.write(peer_id, f"На сервере сейчас {players.online}/{players.max}")
            case "!id":
                logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
                self.write(peer_id,
                           f"Твой ID: {from_id}\n"
                           f"Роль: {self.perms.get_role(from_id)}\n"
                           f"Ник: {self.perms.get_nick(from_id)}")

    def listen(self):
        server, key, ts = self.get_lp_server()
        logger.info("[BOT] Начинаю получать сообщения..")
        while True:
            lp = requests.get(f'{server}?act=a_check&key={key}&ts={ts}&wait=25').json()
            try:
                if lp.get('failed') is not None:
                    key = self.get_lp_server()[1]
                if ts != lp.get('ts') and lp.get('updates'):
                    updates = lp['updates'][0]
                    if updates['type'] == "message_new":
                        self.message_handle(updates['object']['message'])
                ts = lp.get('ts')
            except Exception as i:
                ts = lp.get('ts')
                logger.exception(i)

    def stop(self):
        self.hosts.unload()
