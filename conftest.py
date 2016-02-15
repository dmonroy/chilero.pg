import psycopg2

from chilero.pg.test import TEST_DB_SUFFIX
from chilero.pg.utils import drop_database, create_database, parse_pgurl


def pytest_configure():
    db_url = 'postgres://postgres@localhost:5432/chilero_pg_{}'.format(
        TEST_DB_SUFFIX
    )
    # Drop old test database, if exists
    drop_database(db_url)

    # Create a new, empty, test database
    create_database(db_url)

    # Fill the test database with initial structure
    dbdata = parse_pgurl(db_url)
    conn = psycopg2.connect(**dbdata)
    conn.set_isolation_level(0)
    cur = conn.cursor()
    with open('tests/data/db.sql') as f:
        cur.execute(f.read())
    cur.close()
    conn.close()
