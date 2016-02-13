import asyncio
import json
import random
import string

from aiohttp import request
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

    def _random_string(self, length=12):
        return ''.join(
            random.choice(string.ascii_lowercase) for i in range(length)
        )

    @asyncio.coroutine
    def _create(self, path, data):
        resp = yield from request(
            'POST', self.full_url(path), loop=self.loop,
            data=json.dumps(data)
        )
        return resp

    @asyncio.coroutine
    def _create_and_get(self, path, data):
        resp = yield from self._create(path, data)
        url = resp.headers['Location']
        resp.close()

        resp2 = yield from request(
            'GET', url, loop=self.loop,
        )
        jresp2 = yield from resp2.json()
        resp2.close()
        return jresp2['body']
