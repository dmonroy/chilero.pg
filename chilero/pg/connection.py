import asyncio

import aiopg
from chilero.pg.utils import parse_pgurl


@asyncio.coroutine
def get_pool(**kwargs):  # pragma: no cover
    '''
    Gets the postgresql connection pool.

    :return: pool
    '''
    db_url = kwargs.pop('db_url')
    kwargs.update(parse_pgurl(db_url))

    pool = yield from aiopg.create_pool(**kwargs)

    return pool
