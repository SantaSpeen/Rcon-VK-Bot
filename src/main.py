import sys
import traceback

import requests
import vk

from modules import log, config, rcon, perms, get_server_status


class Bot:

    def __init__(self):
        self.vk = vk.API(access_token=config.vk.token, v=5.199)
        self.group_id = vk.groups.getById()[0]['id']
        with open('help_message.txt') as f:
            self.help_message = f.read()
        log(f"[BOT] ID группы: {self.group_id}")

    def get_lp_server(self):
        lp = vk.groups.getLongPollServer(group_id=self.group_id)
        return lp.get('server'), lp.get('key'), lp.get('ts')

    def write(self, peer_id, message):
        if len(message) > 4095:
            messages = (len(message) // 4095)
            for i in range(1, messages + 1):
                if i > 30:
                    log("[BOT] Сообщение слишком длинное...", 1)
                    break
                self.write(peer_id, message[:4095 * i])
        else:
            vk.messages.send(message=message, peer_id=peer_id, random_id=0)

    def rcon_cmd_handle(self, cmd, from_id, peer_id, _write=True, _allow=False):
        a, r = perms.is_allowed(from_id, cmd.split()[0])
        if _allow:
            r = cmd
        if a or _allow:
            answer = rcon(cmd)
            log(f"[BOT] User: {from_id}({r}) in Chat: {peer_id} use RCON cmd: \"{cmd}\", with answer: \"{answer}\"")
            if _write:
                self.write(peer_id, f"RCON:\n{answer}")
            else:
                return answer
        else:
            log(f"[BOT] User: {from_id}({r}) in Chat: {peer_id} no have rights RCON cmd: \"{cmd}\".")

    def message_handle(self, message):
        from_id = message['from_id']
        peer_id = message['peer_id']
        text = message['text']
        match text:
            case i if i.startwith(".rcon "):
                self.rcon_cmd_handle(i[6:], from_id, peer_id)
            case "!help":
                self.write(peer_id, self.help_message)
            case "!online":
                online = get_server_status().online
                self.write(peer_id, f"На сервере сейчас {online} {""}")
            case "!id":
                self.write(peer_id, f"Твой ID: {from_id}\nРоль: {perms.get_role(from_id)}")

    def listen(self):
        server, key, ts = self.get_lp_server()
        log("[BOT] Начинаю получать сообщения..")
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

            except KeyboardInterrupt as e:
                raise e

            except Exception as e:
                ts = lp.get('ts')
                log(f"Found exception: {e}", 1)
                traceback.print_exc()


if __name__ == '__main__':
    if not config.vk.token:
        log("Токен ВК не найден.\nВыход...", 1)
        input("\n\nНажмите Enter для продолжения..")
        sys.exit(1)
    try:
        bot = Bot()
        try:
            # Test RCON
            bot.rcon_cmd_handle("list", 0, 0, False, True)
            log("RCON работает.")
        except Exception as e:
            log("RCON не отвечает. Проверьте блок \"rcon\" с config.json", 1)
            raise e
        try:
            # Test Minecraft Server
            log(f"Проверка сервера. Онлайн: {get_server_status().online}")
        except Exception as e:
            log("Сервер не отвечает. Проверьте блок \"minecraft\" с config.json", 1)
            raise e
        bot.listen()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log(f"Exception: {e}", 1)
        traceback.print_exc()
    finally:
        log("Выход..")
        input("\n\nНажмите Enter для продолжения..")
