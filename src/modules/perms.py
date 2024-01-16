import os.path
from pathlib import Path

from loguru import logger

from modules import yaml, raw_config_perms, enter_to_exit


class Permissions:
    perm_file = Path("permissions.yml")

    def __init__(self, **kwargs):
        logger.debug(f"[PERMS] Initializing Permissions")
        logger.debug(f"[PERMS] {kwargs=}")
        self._no_role = kwargs.get("noRole")
        self._no_nick = kwargs.get("noNick")
        self.no_rights = kwargs.get("noRights")
        self._perms = kwargs.get('perms')
        if not self._perms or not isinstance(self._perms, dict):
            logger.error(f"[PERMS] Блок: {"perms"!r}, в {self.perm_file!r} - Не валидный")
            logger.debug(f"perms: {type(self._perms)}")
            logger.debug(self._perms)
            enter_to_exit()
        self._nicks = kwargs.get('nicks', {})
        self._members = {}
        self.__handle_members()
        logger.info(f"[PERMS] Права загружены")

    def __handle_parents(self, p=None):
        if p is None:
            p = {}
        for parent, v in self._perms.items():
            for child in v.get("parent", []):
                p[child] = parent
                if p.get(child) == parent and p.get(parent) == child:
                    logger.warning(f"[PERMS] Рекурсивное присваивание запрещено: "
                                   f"perms.{child}.parent.{parent} - perms.{parent}.parent.{child} ({self.perm_file!r})")
                    del p[parent]

        for child, parent in p.items():
            _parent = self._perms.get(child)
            if _parent:
                logger.debug(f"[PERMS] Add {child}.allow to {parent}.allow")
                self._perms[parent]['allow'] += self._perms[child]['allow']
                logger.debug(self._perms[parent]['allow'])
            else:
                logger.warning(f"[PERMS] Группа {child!r} - не найдена (perms.{parent}.parent.{child})")

    def __handle_members(self):
        self.__handle_parents()
        for role, role_data in self._perms.items():
            members = role_data.get("ids", [])
            allow = set(role_data.get("allow", []))
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
        logger.debug(f"{self._members=}")

    def is_allowed(self, member: int, _perms: str | list) -> tuple[bool, str]:
        if isinstance(_perms, str):
            _perms = [_perms]
        for perm in _perms:
            user = self._members.get(member)
            if user:
                friendly = user['friendly']
                allow = user['allow']
                if (("*" in allow) or (perm in allow)) and (f"-{perm}" not in allow):
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
