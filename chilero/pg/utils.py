import os
from urllib.parse import urlsplit


def parse_pgurl(url):
    '''
    Given a Postgres url, return a dict with keys for user, password,
    host, port, and database.
    '''
    parsed = urlsplit(url)

    return {
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path.lstrip('/'),
        'host': parsed.hostname,
        'port': parsed.port or 5432,
    }


def create_database(db_url=None, super_db_url=None):  # pragma: no cover
    '''
    Creates the postgresql database.
    '''
    import psycopg2  # isort:skip

    super_dbdata = parse_pgurl(
        super_db_url or os.getenv(
            'SUPER_DATABASE_URL',
            'psycopg2+postgresql://postgres@localhost:5432/postgres'
        )
    )
    db_url = db_url or os.getenv('DATABASE_URL')
    assert db_url is not None

    dbdata = parse_pgurl(db_url)
    conn = psycopg2.connect(**super_dbdata)
    conn.set_isolation_level(0)
    cur = conn.cursor()

    cur.execute('CREATE DATABASE {}'.format(dbdata['database']))
    cur.close()
    conn.close()


def drop_database(db_url=None, super_db_url=None):  # pragma: no cover
    '''
    Deletes the existing postgresql database.
    '''
    import psycopg2  # isort:skip

    super_dbdata = parse_pgurl(
        super_db_url or os.getenv(
            'SUPER_DATABASE_URL',
            'psycopg2+postgresql://postgres@localhost:5432/postgres'
        )
    )
    db_url = db_url or os.getenv('DATABASE_URL')
    assert db_url is not None

    dbdata = parse_pgurl(db_url)
    conn = psycopg2.connect(**super_dbdata)
    conn.set_isolation_level(0)
    cur = conn.cursor()

    cur.execute('DROP DATABASE IF EXISTS {}'.format(dbdata['database']))
    cur.close()
    conn.close()
