from chilero.pg import parse_pgurl


def test_parse_pgurl():
    pg0 = parse_pgurl(
        'psycopg2+postgresql://postgres@localhost/test'
    )

    assert pg0['user'] == 'postgres'
    assert pg0['password']== None
    assert pg0['database'] == 'test'
    assert pg0['host'] == 'localhost'
    assert pg0['port'] == 5432

    pg1 = parse_pgurl(
        'psycopg2+postgresql://postgres@localhost:5432/test'
    )

    assert pg1['user'] == 'postgres'
    assert pg1['password']== None
    assert pg1['database'] == 'test'
    assert pg1['host'] == 'localhost'
    assert pg1['port'] == 5432

    pg2 = parse_pgurl(
        'psycopg2+postgresql://other:secret@host:15432/testing'
    )

    assert pg2['user'] == 'other'
    assert pg2['password'] == 'secret'
    assert pg2['database'] == 'testing'
    assert pg2['host'] == 'host'
    assert pg2['port'] == 15432
