import asyncio
import random
import sys

from chilero.pg.utils import create_database, drop_database
from chilero.web.test import WebTestCase

from .application import Application


class TestCase(WebTestCase):
    application = Application
    settings = {}

    @asyncio.coroutine
    def initialize_application(self):
        return self.application(
            routes=self.routes,
            settings=self.settings,
            loop=self.loop
        )

    @classmethod
    def setUpClass(cls):
        version = '{}{}{}'.format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )

        dyn_db_url = 'postgres://postgres@localhost/test_{version}'.format(
            version=version
        )

        db_url = '{base}_{name}_{rand}'.format(
            base=cls.settings.get('db_url') or dyn_db_url,
            name=cls.__name__,
            rand=random.randrange(1000, 100000)
        )

        db_url = str(db_url.lower())

        cls.settings['db_url'] = db_url

        cls._database_name = db_url
        cls._initialize_db()

    @classmethod
    def tearDownClass(cls):
        cls._destroy_db()

    @classmethod
    def _initialize_db(cls):
        create_database(cls._database_name)
        if hasattr(cls, '_migrate'):
            cls._migrate(cls._database_name)

    @classmethod
    def _destroy_db(cls):
        drop_database(cls._database_name)
