import json
import traceback
from datetime import datetime

import requests
import vk
from mcrcon import MCRcon


def log(text, lvl=0):
    print(f"[{datetime.now()}] [{['INFO ', 'ERROR'][lvl]}] {text}")


log("Starting..")
with open('config.json') as f:
    config = json.load(f)

vk = vk.API(access_token=config['vk']['token'], v=5.131)
group_id = vk.groups.getById()[0]['id']
log(f"Group id: {group_id}")
admins = config['vk']['admins']

host = config['rcon']['host']
port = config['rcon']['port']
password = config['rcon']['password']


def fix_rcon_text(_srt):
    try:
        _srt = list(_srt)
        for i in range(len(_srt)):
            if _srt[i] == '§':
                _srt[i] = ''
                _srt[i + 1] = ''
            _srt = ''.join(_srt)
    except Exception as e:
        log(f"fix_rcon_text ERROR with: {_srt}", 1)
        _srt = f'CRITICAL ERROR: {e}'
    return _srt


def rcon(cmd):
    try:
        with MCRcon(host, password, port) as mcr:
            return fix_rcon_text(mcr.command(cmd))
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
            write(peer_id, message[:4095*i])
    else:
        vk.messages.send(message=message, peer_id=peer_id, random_id=0)


def rcon_cmd_handle(cmd, from_id, peer_id, _write=True):
    answer = rcon(cmd)
    log(f"User: {from_id} in Chat: {peer_id} use RCON cmd: \"{cmd}\", with answer: \"{answer}\"")
    if _write:
        write(peer_id, f"RCON:\n{answer}")
    else:
        return answer


def main():
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
                    message = updates['object']['message']
                    from_id = message['from_id']
                    peer_id = message['peer_id']
                    text = message['text']
                    if from_id in admins:
                        if text.startswith(".rcon "):
                            rcon_cmd_handle(text[6:], from_id, peer_id)
                        elif text.startswith(".wl "):
                            rcon_cmd_handle(f'whitelist add {text[4:]}', from_id, peer_id)
                    if text == "!help":
                        write(peer_id, "Тебе не нужна помощь, ты и так безпомощный, кожанный улюдок. "
                                       "Так уж и быть, подскажу пару команд..\n\n"
                                       "!help - Вывести эту \"справку\"\n"
                                       "!online - Показать текущий онлайн сервере\n\n"
                                       "Бот сделан кожанным петухом - админом, все вопросы к нему, я не причём.")
                    elif text == "!online":
                        text = rcon_cmd_handle('list', from_id, peer_id, False).replace("\n", "")
                        now = text[10:11]
                        write(peer_id, f"Сейчас играет {now} человек" + ("" if now == "0" else f": {text[43:]}"))

            ts = lp.get('ts')

        except KeyboardInterrupt:
            print('\nExiting...')
            exit(0)

        except Exception as e:
            ts = lp.get('ts')
            print(f"Found exception: {e}")
            print(traceback.format_exc())


if __name__ == '__main__':
    main()
