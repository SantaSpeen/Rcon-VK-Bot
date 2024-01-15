import os.path
from pathlib import Path

from loguru import logger

from modules import yaml, raw_config_perms


class Permissions:
    perm_file = Path("permissions.yml")

    def __init__(self, **kwargs):
        self._no_role = kwargs.get("noRole")
        self._no_nick = kwargs.get("noNick")
        self.no_rights = kwargs.get("noRights")
        self._perms = kwargs['perms']
        self._nicks = kwargs['nicks']
        self._members = {}
        self.__handle_members()
        logger.info(f"[PERMS] Права загружены")

    def __handle_members(self):
        for role, role_data in self._perms.items():
            members = role_data.get("ids", [])
            allow = role_data.get("allow", [])
            allow = set(allow)
            if len(allow) > 0:
                for member in members:
                    if member in self._members:
                        self._members[member]["allow"] |= allow
                    else:
                        self._members[member] = {
                            "role": role,
                            "friendly": role_data.get("name", role),
                            "nick": self._nicks.get(member) or self._no_nick,
                            "allow": allow
                        }

    def is_allowed(self, member, cmd):
        u = self._members.get(member)
        if u:
            friendly = u['friendly']
            allow = u['allow']
            if ("*" in allow) or (cmd in allow):
                return True, friendly
            return False, friendly
        return False, self._no_role

    def get_role(self, member):
        u = self._members.get(member)
        if u:
            return u['friendly']
        return self._no_role

    def get_nick(self, member):
        u = self._members.get(member)
        if u:
            return u.get("nick")
        return self._no_nick

    @classmethod
    def load(cls):
        if os.path.exists(cls.perm_file):
            data = yaml.load(cls.perm_file)
            if not data:
                os.remove(cls.perm_file)
                return Permissions.load()
        else:
            logger.info(f"Создание: {cls.perm_file}...")
            data = yaml.load(raw_config_perms)
            with open(cls.perm_file, mode="w", encoding="utf-8") as f:
                yaml.dump(data, f)

        logger.info(f"[PERMS] {cls.perm_file} - загружен")
        return Permissions(**data)


if __name__ == '__main__':
    perms = Permissions.load()
