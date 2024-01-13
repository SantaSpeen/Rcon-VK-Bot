import sys

import requests
import vk
from loguru import logger

from modules import config, rcon, get_server_status, enter_to_exit, Permissions, __version__, new_version


class Bot:

    def __init__(self):
        self.vk = vk.API(access_token=config.vk.token, v=5.199)
        self.group_id = self.vk.groups.getById()['groups'][0]['id']
        with open('help_message.txt', encoding="utf-8") as f:
            self.help_message = f.read()
        logger.info(f"[BOT] ID группы: {self.group_id}")

    def get_lp_server(self):
        lp = self.vk.groups.getLongPollServer(group_id=self.group_id)
        return lp.get('server'), lp.get('key'), lp.get('ts')

    def write(self, peer_id, message):
        if len(message) > 4095:
            messages = (len(message) // 4095)
            for i in range(1, messages + 1):
                if i > 30:
                    logger.error("[BOT] Сообщение слишком длинное...")
                    break
                self.write(peer_id, message[:4095 * i])
        else:
            self.vk.messages.send(message=message, peer_id=peer_id, random_id=0)

    def rcon_cmd_handle(self, cmd, from_id, peer_id, _write=True, _allow=False):
        a, r = perms.is_allowed(from_id, cmd.split()[0])
        if _allow:
            r = cmd
        if a or _allow:
            answer = rcon(cmd)
            logger.info(f"[BOT] User: {from_id}({r}) in Chat: {peer_id} use RCON cmd: \"{cmd}\", "
                        f"with answer: \"{answer}\"")
            if _write:
                self.write(peer_id, f"RCON:\n{answer}")
            else:
                return answer
        else:
            logger.info(f"[BOT] User: {from_id}({r}) in Chat: {peer_id} no have rights RCON cmd: \"{cmd}\".")

    def _bot_handle(self, message):
        from_id = message['from_id']
        global perms
        if perms.is_allowed(from_id, "bot"):
            peer_id = message['peer_id']
            text = message['text']
            logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
            tsplit = text.split(" ")
            cmds = ("Доступные команды:\n"
                    "  .bot help - Вывести это сообщение.\n"
                    "  .bot info - Выводит краткую информацию о боте."
                    "  .bot perm user <> - Добавить пользователя \n"
                    "  .bot perm reload - Перезагружает пермишины")
            if len(tsplit) == 1:
                self.write(peer_id, cmds)
                return
            match tsplit[1]:
                case "perm":
                    match tsplit[2] if len(tsplit) > 2 else None:
                        case "reload":
                            perms = Permissions.load()
                            self.write(peer_id, "Права перезагружены")
                        case _:
                            self.write(peer_id, ".bot perm ?")
                case "info":
                    st = get_server_status()
                    self.write(peer_id, f"RconVkBot\n"
                                        f"Версия бота: {__version__}, последняя: {not new_version}\n"
                                        f"Пинг до сервера: {st.latency:.3f}ms\n"
                                        f"Бедрок: {st.motd.bedrock} ({st.version.protocol})\n")
                case _:
                    self.write(peer_id, cmds)

    def message_handle(self, message):
        from_id = message['from_id']
        peer_id = message['peer_id']
        text = message['text']
        match text:
            case i if i.startswith(".rcon "):
                self.rcon_cmd_handle(i[6:], from_id, peer_id)
            case i if i.startswith(".bot"):
                self._bot_handle(message)
            case "!help":
                logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
                self.write(peer_id, self.help_message)
            case "!online":
                logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
                players = get_server_status().players
                self.write(peer_id, f"На сервере сейчас {players.online}/{players.max}")
            case "!id":
                logger.info(f"[BOT] {peer_id}:{from_id}:{text}")
                self.write(peer_id,
                           f"Твой ID: {from_id}\nРоль: {perms.get_role(from_id)}\nНик: {perms.get_nick(from_id)}")

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


if __name__ == '__main__':
    perms = Permissions.load()
    # Check token
    if not config.vk.token:
        logger.error("Токен ВК не найден.")
        enter_to_exit()
    # Test RCON
    if rcon("list").startswith("Rcon error"):
        logger.error("RCON не отвечает. Проверьте блок \"rcon\" в config.json")
        enter_to_exit()
    logger.info("RCON доступен.")
    # Test Minecraft Server
    try:
        _players = get_server_status().players
        logger.info(f"Проверка сервера. Онлайн: {_players.online}/{_players.max}")
    except Exception as e:
        logger.exception(e)
        logger.info("Сервер не отвечает. Проверьте блок \"minecraft\" в config.json")
        enter_to_exit()
    try:
        bot = Bot()
        bot.listen()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception(e)
        enter_to_exit()
