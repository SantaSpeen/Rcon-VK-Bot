import json
import traceback

import requests
import vk
from mcrcon import MCRcon

print("Starting..")
with open('config.json') as f:
    config = json.load(f)

vk = vk.API(access_token=config['vk']['token'], v=5.131)
group_id = vk.groups.getById()[0]['id']
print(f"Group id: {group_id}")
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
        _srt = f'CRITICAL ERROR: {e}'
    return _srt


def rcon(cmd):
    with MCRcon(host, password, port) as mcr:
        return fix_rcon_text(mcr.command(cmd))


def get_lp_server():
    lp = vk.groups.getLongPollServer(group_id=group_id)
    return lp.get('server'), lp.get('key'), lp.get('ts')


def write(peer_id, message):
    vk.messages.send(message=message, peer_id=peer_id, random_id=0)


def main():
    server, key, ts = get_lp_server()
    print("Listening..")
    while True:
        try:
            lp = requests.get(f'{server}?act=a_check&key={key}&ts={ts}&wait=25').json()
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
                            write(peer_id, f"rcon: {rcon(text[6:])}")
                        elif text.startswith(".wl "):
                            write(peer_id, f"Ok\n{rcon(f'whitelist add {text[4:]}')}")

            ts = lp.get('ts')

        except KeyboardInterrupt:
            print('\nExiting...')
            exit(0)

        except Exception as e:
            print(f"Found exception: {e}")
            print(traceback.format_exc())


if __name__ == '__main__':
    main()
