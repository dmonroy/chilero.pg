import asyncio

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


