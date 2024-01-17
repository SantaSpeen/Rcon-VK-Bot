import os.path
from pathlib import Path

from loguru import logger

from modules import yaml, raw_config_perms, enter_to_exit


class Permissions:
    perms_file = Path("permissions.yml")

    def __init__(self, **kwargs):
        logger.debug(f"[PERMS] Initializing Permissions")
        logger.debug(f"[PERMS] {kwargs=}")
        self._no_role = kwargs.get("noRole")
        self._no_nick = kwargs.get("noNick")
        self.no_rights = kwargs.get("noRights")
        self._perms = kwargs.get('perms')
        if not self._perms or not isinstance(self._perms, dict):
            logger.error(f"[PERMS] Блок: {"perms"!r}, в {self.perms_file!r} - Не валидный")
            logger.debug(f"perms: {type(self._perms)}")
            logger.debug(self._perms)
            enter_to_exit()
        self._nicks = kwargs.get('nicks', {})
        self._members = {}
        self.__handle_members()
        logger.info(f"[PERMS] Права загружены")

    def __handle_parents(self, r=True):
        p = {}
        for parent, v in self._perms.items():
            for child in v.get("parent", []):
                p[child] = parent
                if p.get(child) == parent and p.get(parent) == child:
                    logger.warning(f"[PERMS] Рекурсивное присваивание запрещено: "
                                   f"perms.{child}.parent.{parent} - perms.{parent}.parent.{child} ({self.perms_file!r})")
                    del p[parent]

        for child, parent in p.items():
            _parent = self._perms.get(child)
            if _parent:
                logger.debug(f"[PERMS] Add {child}.allow to {parent}.allow")
                self._perms[parent]['allow'] += self._perms[child]['allow']
                logger.debug(self._perms[parent]['allow'])
            else:
                logger.warning(f"[PERMS] Группа {child!r} - не найдена (perms.{parent}.parent.{child})")

        if r:
            logger.debug(f"[PERMS] Again :)")
            self.__handle_parents(False)

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

    def is_allowed(self, member: int, perms: str | list, raw_role=False) -> tuple[bool, str]:
        if isinstance(perms, str):
            perms = [perms]
        logger.debug(perms)
        allow = False, self._no_role
        user = self._members.get(member)
        if user:
            allow_list = user['allow']
            logger.debug(f"{user=} {allow_list=}")
            role = self.get_role(member, raw_role)
            for perm in perms:
                if f"-{perm}" in allow_list:
                    allow = False, role
                    logger.debug(f"Found -{perm=}")
                    break
                if not allow[0]:
                    if ((("*" in allow_list) or ("bot.*" in allow_list) or (perm in allow_list))
                            and (f"-{perm}" not in allow_list)):
                        allow = True, role
                    else:
                        allow = False, role
        logger.debug(allow)
        return allow

    def get_role(self, member, raw_role=False):
        user = self._members.get(member)
        if user:
            return user['friendly'] if not raw_role else user['role']
        return self._no_role

    def get_nick(self, member):
        u = self._members.get(member)
        if u:
            return u.get("nick")
        return self._no_nick

    @classmethod
    def load(cls):
        if os.path.exists(cls.perms_file):
            data = yaml.load(cls.perms_file)
            if not data:
                os.remove(cls.perms_file)
                return Permissions.load()
        else:
            logger.info(f"Создание: {cls.perms_file}...")
            data = yaml.load(raw_config_perms)
            with open(cls.perms_file, mode="w", encoding="utf-8") as f:
                yaml.dump(data, f)

        logger.info(f"[PERMS] {cls.perms_file} - загружен")
        return Permissions(**data)
