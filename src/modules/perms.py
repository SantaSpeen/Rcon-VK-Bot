import os.path
import sys
from pathlib import Path

from loguru import logger

from modules import yaml


class Permissions:
    perm_file = Path("permissions.yml")

    def __init__(self, **kwargs):
        self._no_role = kwargs.get("noRole")
        self._no_nick = kwargs.get("noNick")
        self.no_rights = kwargs.get("noRights")
        self._perms = kwargs['perms']
        self._members = {}
        if kwargs['useLuckPerms']:
            logger.info("[PERMS] Поддержка LuckPerms всё ещё в разработке. ")
            print(kwargs['LuckPerms']['nicks'])
            sys.exit(1)
        self._luck_perms = kwargs['LuckPerms']
        logger.info(f"[PERMS] {self.perm_file} - загружен")
        self.__handle_members()

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
                            "nick": self._luck_perms['nicks'].get(member) or self._no_nick,
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
            logger.info(f"Generating permissions file: {cls.perm_file}")
            import textwrap
            raw = textwrap.dedent("""\
            noRole: Нет роли
            noRights: Нет прав  # null для отключения
            noNick: Не указан  # Используется для !id, ник берётся из LuckPerms.nicks независимо от useLuckPerms
            perms:
              admins:  # Имя группы
                name: Админ  # Имя группы, которое будет отображаться в боте
                ids:  # вк ИД входящих в состав группы
                - 370926160
                allow:  # Какие команды разрешены, "*" - все
                - '*'
              # Пример настройки
              helpers:
                name: Хелпер
                ids:
                - 583018016
                allow:
                - say
                - mute
                - warn
            
            # Находится в режиме тестирования
            # Интеграция с базой данных LuckPerms (Нужна именно внешняя база данных)
            useLuckPerms: false
            LuckPerms:
            
              # Таблица соответствия vkID к нику в Майнкрафте
              nicks:
                370926160: Rick
                583018016: SantaSpeen
            
              # Разрешенные варианты: MySQL, MariaDB, PostgreSQL
              storage-method: PostgreSQL
              data:
                # Указывайте host:port
                address: 127.0.0.1:5432
                # База данных в которой хранятся настройки LuckPerms
                database: minecraftDB
                # Логин и пароль для доступа к БД
                username: user
                password: user
            
                # Смотрите настройку LuckPerms
                table-prefix: luckperms_
              server: global

            """)
            data = yaml.load(raw)
            with open(cls.perm_file, mode="w", encoding="utf-8") as f:
                yaml.dump(data, f)

        return Permissions(**data)


if __name__ == '__main__':
    perms = Permissions.load()
