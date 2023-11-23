import re
import sys
import json
import traceback
from datetime import datetime

import requests
import vk
from mcrcon import MCRcon


def log(text, lvl=0):
    print(f"[{datetime.now()}] [{['INFO ', 'ERROR'][lvl]}] {text}")


log("Starting..")
with open('config-t.json' if "-t" in sys.argv else 'config.json') as f:
    config = json.load(f)

with open('help_message.txt') as f:
    help_message = f.read()

vk = vk.API(access_token=config['vk']['token'], v=5.131)
group_id = vk.groups.getById()[0]['id']
log(f"Group id: {group_id}")

host = config['rcon']['host']
port = config['rcon']['port']
password = config['rcon']['password']


class Permissions:

    def __init__(self, permission_file):
        self.permission_file = permission_file
        self._raw_file = {}
        self._members = {}
        self._parse_file()

    def _parse_file(self):
        with open(self.permission_file) as pf:
            self._raw_file = json.load(pf)

        for role, role_data in self._raw_file.items():
            members = role_data.get("members", [])
            allow = role_data.get("allow", [])
            for member in members:
                self._members[member] = {
                    "role": role,
                    "allow": allow
                }

    def is_allow(self, vk_id, cmd):
        u = self._members.get(vk_id)
        if u is not None:
            role = u['role']
            allow = u['allow']
            if allow is True:
                return True, role
            elif cmd in allow:
                return True, role
            return False, role
        return False, None

    def get_role(self, vk_id):
        u = self._members.get(vk_id)
        if u is not None:
            return u['role']
        return None


perms = Permissions(config['permission_file'])


def rcon(cmd):
    try:
        with MCRcon(host, password, port) as mcr:
            text = mcr.command(cmd)
            return re.sub(r'§.', '', text)
    except Exception as e:
        log(f"RCON ERROR with command: {cmd}", 1)
        print(traceback.format_exc())
        return f"Rcon error: {e}"


def get_lp_server():
    lp = vk.groups.getLongPollServer(group_id=group_id)
    return lp.get('server'), lp.get('key'), lp.get('ts')


def write(peer_id, message):
    if len(message) > 4095:
        messages = (len(message) // 4095)
        for i in range(1, messages + 1):
            if i > 30:
                log("Found very long message...", 1)
                break
            write(peer_id, message[:4095 * i])
    else:
        vk.messages.send(message=message, peer_id=peer_id, random_id=0)


def rcon_cmd_handle(cmd, from_id, peer_id, _write=True, _allow=False):
    a, r = perms.is_allow(from_id, cmd.split()[0])
    if _allow:
        r = cmd
    if a or _allow:
        answer = rcon(cmd)
        log(f"User: {from_id}({r}) in Chat: {peer_id} use RCON cmd: \"{cmd}\", with answer: \"{answer}\"")
        if _write:
            write(peer_id, f"RCON:\n{answer}")
        else:
            return answer
    else:
        log(f"User: {from_id}({r}) in Chat: {peer_id} no have rights RCON cmd: \"{cmd}\".")


def message_handle(message):
    from_id = message['from_id']
    peer_id = message['peer_id']
    text = message['text']
    if text.startswith(".rcon "):
        rcon_cmd_handle(text[6:], from_id, peer_id)
    if text == "!help":
        write(peer_id, help_message)
    elif text == "!online":
        text = rcon_cmd_handle('list', from_id, peer_id, True, True).replace("\n", "")
        write(peer_id, text)
        # now = text[10:11]
        # write(peer_id, f"Сейчас играет {now} человек" + ("" if now == "0" else f": {text[43:]}"))
    elif text == "!id":
        write(peer_id, f"Твой ID: {from_id}\nРоль в боте: {perms.get_role(from_id) or 'Отсутствует'}")


def listen():
    server, key, ts = get_lp_server()
    log("Listening..")
    while True:
        lp = requests.get(f'{server}?act=a_check&key={key}&ts={ts}&wait=25').json()
        try:
            if lp.get('failed') is not None:
                key = get_lp_server()[1]
            if ts != lp.get('ts') and lp.get('updates'):
                updates = lp['updates'][0]
                if updates['type'] == "message_new":
                    message_handle(updates['object']['message'])

            ts = lp.get('ts')

        except KeyboardInterrupt:
            print('\nExiting...')
            exit(0)

        except Exception as e:
            ts = lp.get('ts')
            print(f"Found exception: {e}")
            print(traceback.format_exc())


if __name__ == '__main__':
    listen()
