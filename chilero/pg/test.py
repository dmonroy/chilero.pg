import asyncio
import json
import random
import string
import sys

from aiohttp import request
from chilero.web.test import WebTestCase

from .application import Application

TEST_DB_SUFFIX = 'test_{}{}{}'.format(
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )


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
    def _get(self, path, **kwargs):
        resp = yield from request('GET', path, loop=self.loop, **kwargs)
        return resp

    @asyncio.coroutine
    def _get_json(self, path, **kwargs):
        resp = yield from self._get(path, **kwargs)
        jresp = yield from resp.json()
        resp.close()
        return jresp

    @asyncio.coroutine
    def _index(self, path):
        resp = yield from self._get_json(self.full_url(path))
        return resp

    @asyncio.coroutine
    def _create(self, path, data):
        resp = yield from request(
            'POST', self.full_url(path), loop=self.loop,
            data=json.dumps(data)
        )
        return resp

    @asyncio.coroutine
    def _create_and_get(self, path, data, defaults=None):
        defaults = defaults or {}
        defaults.update(data)
        resp = yield from self._create(path, defaults)
        if resp.status != 201:
            return resp, None

        url = resp.headers['Location']

        jresp = yield from self._get_json(url)

        return resp, jresp['body']

    @asyncio.coroutine
    def _patch(self, url, **kwargs):
        resp = yield from request(
            'PATCH', url, loop=self.loop,
            data=json.dumps(kwargs)
        )
        return resp

    @asyncio.coroutine
    def _search(self, path, terms):
        resp = self._get_json(
            self.full_url(
                '{endpoint}?search={keywords}'.format(
                    endpoint=path,
                    keywords='+'.join(terms.split())
                )
            )
        )
        return resp
