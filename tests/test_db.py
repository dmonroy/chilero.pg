import sys

from chilero.pg.test import TestCase


class TestDBFromSettings(TestCase):
    settings = dict(
        db_url='postgres://postgres@localhost/fixed_db_name'
    )
    def test_db_name(self):
        assert self._database_name.startswith(
            'postgres://postgres@localhost/fixed_db_name_TestDBFromSettings_'
        )


class TestRandomDB(TestCase):
    def test_db_name(self):
        version = '{}{}{}'.format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )
        assert self._database_name.startswith(
            'postgres://postgres@localhost/test_{version}_TestRandomDB_'.format(
                version=version
            )
        )
