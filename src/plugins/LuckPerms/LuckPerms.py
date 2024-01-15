try:
    import Bot
    import logger
except ImportError:
    Bot = object


class Plugin(Bot):

    ac_dir = "./perms"

    def __init__(self):
        super(Plugin, self).__init__()
        logger.info(f"Инициализация {self.name} v{self.version}")

    async def load(self):
        pass

    async def unload(self):
        pass
