# RCON бот для ВК сообществ

**Не забывай про звёздочку!)**

## Что умеет: 

### Команды 

<p style="color: red">Не стесняйтесь, предлагайте свои идеи в issue, Vk, Telegram</p>

* Доступные разрешённым людям
  * **`.rcon <command>`** - Исполняет <*command*> и показывает ответ сервера
  * **`.bot`** - Команды бота, требует разрешения `bot`
* Доступные всем
  * **`!help`** - Выводит страничку с командами (Текст в файле help_message.txt)
  * **`!online`** - Запрашивает у сервера онлайн и выводит
  * **`!id`** - Выводит ID пользователя, и его роль

### Возможности

* Система [permissions](#система-permissions):
  * Локально 
  * Интеграция с LuckPerms (В разработке)

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

## Система permissions

В файле `permissions.yml` указаны все пользователи с "повышенным" уровнем доступа к боту\
Пример
```yaml
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
```

**Интеграция с LuckPerms ещё не готова!**

### За помощью, заказами и предложениями можно обратиться сюда:

1. _Vk_ [@l.vindeta](https://vk.me/l.vindeta)
2. _Telegram_ [@id01234](https://t.me/id0124)

Мб что-нибудь ещё добавлю :)
