import time
from datetime import datetime
from threading import Thread

from loguru import logger
from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class OnlineStats(Base):
    __tablename__ = 'online_stats'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    users_online = Column(Integer)


class History:

    def __init__(self):
        self.hosts = None
        self.thread = None
        self.stop = False
        self.engine = create_engine('sqlite:///./stats.db', echo=False)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def _run(self):
        while not self.stop:
            time.sleep(1)

    def load(self, hosts):
        self.unload()
        self.stop = False
        self.hosts = hosts
        self.thread = Thread(target=self._run)
        self.thread.start()
        logger.info("[HOSTS] Поток для отслеживания запущен")
        return self

    def unload(self, stop=False):
        """Останавливает поток"""
        if self.thread:
            self.stop = True
            self.thread.join()
            self.thread = None
        if stop:
            self.session.close()

