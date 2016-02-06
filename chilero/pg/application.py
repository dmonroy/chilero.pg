import asyncio

from chilero.pg.connection import get_pool
from chilero.web import Application as BaseApplication


class Application(BaseApplication):

    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop('settings') or {}
        super(BaseApplication, self).__init__(*args, **kwargs)

    @asyncio.coroutine
    def get_pool(self):
        if not hasattr(self, 'db_pool'):
            self.db_pool = yield from get_pool(
                db_url=self.settings.get('db_url'),
                minsize=self.settings.get('db_pool_min') or 0,
                maxsize=self.settings.get('db_pool_max') or 10
            )

        return self.db_pool

    @asyncio.coroutine
    def close_pool(self):
        yield from self.db_pool.finish()

    @asyncio.coroutine
    def finish(self):
        yield from self.close_pool()

        yield from super(Application, self).finish()
