import asyncio
import random

import sys
from chilero.web.test import WebTestCase

from chilero.pg.utils import create_database, drop_database
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
        cls._database_name = 'test_{version}_{name}_{rand}'.format(
            version=version,
            name=cls.__name__,
            rand=random.randrange(1000, 100000)
        )
        cls._initialize_db()

    @classmethod
    def tearDownClass(cls):
        cls._destroy_db()


    @classmethod
    def _initialize_db(cls):
        create_database(cls._database_name)

    @classmethod
    def _destroy_db(cls):
        drop_database(cls._database_name)

