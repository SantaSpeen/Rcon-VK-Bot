from mcrcon import MCRcon



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


def main():
    pass


if __name__ == '__main__':
    main()
