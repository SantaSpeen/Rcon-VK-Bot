# RCON бот для ВК сообществ
[![CodeTime badge](https://img.shields.io/endpoint?style=flat&url=https%3A%2F%2Fapi.codetime.dev%2Fshield%3Fid%3D24004%26project%3D%26in%3D0)](https://github.com/SantaSpeen/)

**Не забывай про звёздочку!)**
## Что умеет: 

### Команды 

**Не стесняйтесь, предлагайте свои идеи в issue, Vk, Telegram**\
Бот использует по умолчанию хост - *default*, т.е. `.rcon default say hello` такое же что и `.rcon say hello`

* **`.rcon (<host> | default) <command>`** - Исполняет <*command*> на <*host*> и показывает ответ сервера (`bot.rcon.<host>` и `bot.rcon.<host>.<command>`)


* **`.bot`** - Команды бота (`bot.help`)
* **`.bot help`** - Команды бота (`bot.help`)
* **`.bot info`** - Выводит краткую информацию о боте. (`bot.info`)
* **`.bot hosts list`** - Список доступных хостов. (`bot.hosts.list`)
* **`.bot hosts reload`** - Перезагружает hosts.yml. (`bot.hosts.reload`)
* **`.bot perms reload`** - Перезагружает permissions.yml. (`bot.perms.reload`)


* **`!help`** - Выводит содержимое help_message.txt (`bot.cmd.help`)
* **`!id`** - Выводит ID пользователя, его роль и ник (`bot.cmd.id`)
* **`!online (<host> | default)`** - Запрашивает у <*host*> онлайн и выводит (`bot.cmd.online.<host>`)
* **`!history (<host> | default)`** - **(WIP)** Выводит график онлайна на <*host*> (`bot.cmd.history.<host>`)

### Возможности

* Работа в [Docker](./Dockerfile)


* Система [Permissions](#система-permissions) - Разрешения для пользователей
* Система [MultiHost](#система-multihost) - Если у тебя очень много хостов

## Как запустить?

### Скачать скомпилированный вариант

* [Страница релизов](https://github.com/SantaSpeen/Rcon-VK-Bot/releases)

### Запуск напрямую 

1. Должен быть установлен Python3.12 (**На версиях ниже не будет работать**)
2. Качаем репозиторий
3. `pip install -r requirements.txt` - Установка зависимостей
4. 1 Раз запускаем, что бы сгенерировалось всё что нужно
5. Лезем в `config.json`, `permissions.yml` и настраиваем
6. `python main.py` - Запускаем
7. [Опционально] Скомпилировать `pyinstaller --noconfirm --onefile --console --icon "./win/icon.ico" --name "Rcon-VK-Bot" --version-file "./win/version.txt"  "./src/main.py"`

_Всё очень легко и просто)_

## Система Permissions
Файл: `config/permissions.yml`\
В файле указаны **vk id** пользователей и их разрешения\
Стандартный вид:
```yaml
noRole: Нет роли
noRights: Нет прав  # null для отключения
noNick: Не указан  # Используется для !id

# Таблица соответствия vkID к нику в Майнкрафте
# Ник будет передаваться в плагины (Плагины бота)
nicks:
  370926160: Rick
  583018016: SantaSpeen

perms:
  admin:  # Имя группы
    name: Админ  # Имя группы, которое будет отображаться в боте
    ids:  # вк ИД входящих в состав группы
    - 370926160
    parent:  # Наследование прав
    - helper
    allow:  # Какие команды разрешены, "*" - все
    - '*'
  helper:
    name: Хелпер
    ids:
    - 583018016
    allow:
    - bot.rcon.*    # См. host.yml
    - say
    - mute
    - warn
  default:
    name: Игрок
    allow:
    - bot.cmd.help
    - bot.cmd.id
    - bot.cmd.online.*
    - bot.cmd.history.*
```

## Система MultiHost
Файл: `config/hosts.yml`\
Тут должно быть описание..\
Стандартный вид:
```yaml
hosts:
  survival:  # Название сервера (имя), может быть любым, может быть сколько угодно
    meta:
      name: Выживание  # Это имя будет выводиться в ответе, или статистике (имя для бота)
      java: true  # Это JAVA сервер?
      important: true  # Если да, то бот не включится, если не подключится
      # 0 - выключен
      # 1 - Доступно без имени (!! Такое значение может быть только у 1 хоста !!) (.rcon <cmd>)
      # 2 - Доступно с именем (.rcon <name> <cmd>)
      # Разрешение: bot.rcon.<name>; bot.online.<name>; bot.history.<name>
      # При запуске бота будет проверка доступности всего
      rcon: 2  # RCON будет доступен по команде .rcon lobby <cmd> (разрешение: bot.rcon.lobby)
      # !online будет доступен по команде !online lobby (разрешение: bot.cmd.online.lobby)
      # !history будет доступен по команде !history lobby (разрешение: bot.cmd.history.lobby)
      online: 2
    rcon:  # RCON подключение
      host: 192.168.0.31
      port: 15101
      password: rconPass1
    mine:  # Minecraft подключение (нужно для !online и !history)
      host: 192.168.0.31
      port: 15001

  lobby:
    meta:
      name: Лобби
      important: true
      java: true
      rcon: 1
      online: 2
    rcon:
      host: 192.168.0.31
      port: 15100
      password: rconPass2
    mine:
      host: 192.168.0.31
      port: 15000

  devlobby:
    meta:
      name: Лобби
      important: false
      java: true
      rcon: 2
      online: 2
    rcon:
      host: 192.168.0.31
      port: 15108
      password: rconPass3
    mine:
      host: 192.168.0.31
      port: 15008

  proxy-local:
    meta:
      name: Proxy-Local
      java: true
      important: true
      rcon: 0
      online: 1
    rcon:
    mine:
      host: 192.168.0.31
      port: 15009
```

### За помощью, заказами и предложениями можно обратиться сюда:

1. _Vk_ [@l.vindeta](https://vk.me/l.vindeta)
2. _Telegram_ [@id01234](https://t.me/id0124)

Мб что-нибудь ещё добавлю :)
