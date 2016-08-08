import asyncio
import random

import names
from chilero.web.test import asynctest

from chilero.pg import Resource
from chilero.pg.test import TestCase, TEST_DB_SUFFIX


class Friends(Resource):
    order_by = 'name ASC'
    search_fields = ['name']
    allowed_fields = ['name']
    required_fields = ['name']
    allow_order_by = ['name']

    def serialize_object(self, row):
        return dict(
            id=row[0],
            name=row[1],
            url=self.get_object_url(row[0])
        )


class BaseTestCase(TestCase):
    settings = dict(
        db_url='postgres://postgres@localhost:5432/chilero_pg_{}'.format(
            TEST_DB_SUFFIX
        )
    )
    routes = [
        ['/friends', Friends]
    ]

    @asyncio.coroutine
    def _create_friend(self, **kwargs):
        defaults = dict(
            name=self._random_string()
        )

        return(
            yield from self._create_and_get('/friends', kwargs, defaults)
        )


class TestAdvancedOptions(BaseTestCase):

    @asyncio.coroutine
    def _a_lot_of_friends(self):
        # create a lot of friends
        all_names = []
        for i in range(100):
            name = names.get_full_name()
            all_names.append(name)
            _, f = yield from self._create_friend(name=name)
            _.close()
        return all_names

    @asynctest
    def test_pagination(self):

        yield from self._a_lot_of_friends()

        # list with default values
        # page 1
        r = yield from self._get_json(self.full_url('/friends'))
        assert r['data']['count'] >= 100
        assert r['data']['prev'] == None
        assert 'offset=20' in r['data']['next']
        assert 'limit=20' in r['data']['next']
        assert len(r['index']) == r['data']['length']

        # page 2
        r = yield from self._get_json(r['data']['next'])
        assert 'offset=0' in r['data']['prev']
        assert 'offset=40' in r['data']['next']
        assert len(r['index']) == r['data']['length']

    @asynctest
    def test_pagination_no_limit(self):

        yield from self._a_lot_of_friends()

        # list with no limit
        r = yield from self._get_json(self.full_url('/friends?limit=0'))

        assert r['data']['count'] >= 100
        assert r['data']['prev'] == None
        assert r['data']['next'] == None
        assert r['data']['length'] == r['data']['count']
        assert len(r['index']) == r['data']['count']

    @asynctest
    def test_search_pagination(self):
        rnames = list((yield from self._a_lot_of_friends()))
        rname = random.choice(rnames).split()[0]
        for i in range(5):
            name = '{} {}'.format(rname, names.get_last_name())
            _, friend = yield from self._create_friend(name=name)
            _.close()

        rname = rname.lower()

        r = yield from self._get_json(
            self.full_url('/friends?search={}&limit=1'.format(rname))
        )

        assert r['data']['count'] >= 1
        assert rname in r['data']['next']

        while r['data']['next']:
            r = yield from self._get_json(r['data']['next'])
            if r['data']['next'] is not None:
                assert rname in r['data']['next']
            assert rname in r['data']['prev']
            rname.lower() in r['index'][0]['name'].lower()

    @asynctest
    def test_oreder_by_ASC(self):
        yield from self._a_lot_of_friends()
        name = 'Abel Barrera'
        _, friend = yield from self._create_friend(name=name)
        _.close()
        url = self.full_url('/friends?order_by={}'.format('name'))
        resp = yield from self._get_json(url)
        assert resp['index'][0]['name'].startswith('A')

    @asynctest
    def test_oreder_by_400(self):
        yield from self._a_lot_of_friends()
        url = self.full_url('/friends?order_by={}'.format('other'))
        resp = yield from self._get(url)
        assert resp.status == 400

    @asynctest
    def test_oreder_by_desc(self):
        yield from self._a_lot_of_friends()
        defaults = dict(
            name='Zarahi zuna'
        )
        resp = yield from self._create('/friends', defaults)
        assert resp.status == 201
        resp.close()
        url = self.full_url('/friends?order_by={}'.format('-name'))
        resp = yield from self._get_json(url)
        assert resp['index'][0]['name'].startswith('Z')


class TestBasic(BaseTestCase):
    # Test common REST actions

    @asynctest
    def test_index(self):
        resp = yield from self._get(self.full_url('/friends'))

        assert resp.status == 200
        resp.close()

    @asynctest
    def test_index_json(self):
        resp = yield from self._index('/friends')
        assert isinstance(resp, dict)
        assert 'index' in resp

    @asynctest
    def test_create(self):
        name = self._random_string()
        _, friend = yield from self._create_friend(name=name)
        assert _.status == 201
        _.close()
        assert friend['name'] == name
        efriend = yield from self._delete(friend['url'])
        assert efriend.status==200

    @asynctest
    def test_create_error(self):
        _, friend = yield from self._create_friend(wrong_field=123)
        assert _.status == 400
        _.close()

    @asynctest
    def test_create_conflict(self):
        name = names.get_full_name()
        _, friend = yield from self._create_friend(name=name)
        _.close()
        _, friend = yield from self._create_friend(name=name)
        assert _.status == 409
        _.close()


    @asynctest
    def test_update(self):
        _, friend = yield from self._create_friend()
        _.close()

        new_name = self._random_string()

        presp = yield from self._patch(friend['url'], name=new_name)

        assert presp.status == 204
        presp.close()

        updated_friend = yield from self._get_json(friend['url'])
        assert updated_friend['body']['name'] == new_name

    @asynctest
    def test_search(self):
        name = 'some known name'
        _, friend = yield from self._create_friend(name=name)
        _.close()
        results = yield from self._search('/friends', terms='known name')

        assert len(results['index']) > 0
        assert results['index'][0]['name'] == name

    @asynctest
    def test_view_404(self):
        resp = yield from self._get(self.full_url('/friends/999999'))
        assert resp.status == 404
        resp.close()

    @asynctest
    def test_update_400(self):
        _, friend = yield from self._create_friend()
        _.close()

        new_name = self._random_string()

        presp = yield from self._patch(friend['url'], names=new_name)

        assert presp.status == 400
        presp.close()

    @asynctest
    def test_update_empty_required_400(self):
        _, friend = yield from self._create_friend()
        _.close()

        new_name = "   "

        presp = yield from self._patch(friend['url'], name=new_name)

        assert presp.status == 400
        presp.close()

    @asynctest
    def test_update_None_required_400(self):
        _, friend = yield from self._create_friend()
        _.close()

        new_name = None

        presp = yield from self._patch(friend['url'], name=new_name)

        assert presp.status == 400
        presp.close()
