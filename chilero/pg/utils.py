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
