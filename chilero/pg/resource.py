import asyncio
import json
import os
from urllib.parse import quote_plus

from aiohttp.web_exceptions import HTTPBadRequest, HTTPConflict, HTTPNotFound
from chilero.web import Resource as BaseResource
from chilero.web import Response
from psycopg2._psycopg import DatabaseError


class Resource(BaseResource):
    list_query = 'SELECT * from {table}'
    object_query = 'SELECT * FROM {table}'
    table_name = None
    count_query = 'SELECT count(1) from {table}'
    order_by = 'id'
    id_column = 'id'
    allowed_fields = []
    required_fields = []
    search_fields = None
    allow_order_by = []

    @asyncio.coroutine
    def get_pool(self):
        return self.app.get_pool()

    @asyncio.coroutine
    def get_cursor(self):
        pool = yield from self.get_pool()
        cursor = yield from pool.cursor()
        return cursor

    def get_count_query(self):
        return self.count_query.format(table=self.get_table_name())

    def get_list_query(self):
        return self.list_query.format(table=self.get_table_name())

    def get_object_query(self):
        return self.object_query.format(table=self.get_table_name())

    def get_list_query_filters(self, conditions=None, search=None):
        query_filters = ''
        query_args = tuple()
        if conditions:
            fields = conditions.keys()
            filters = ', '.join(
                ['{field_name}=%s'.format(field_name=f) for f in fields]
            )
            query_filters = '{query} WHERE {filters}'.format(
                query=query_filters, filters=filters
            )

            query_args = tuple([conditions[f] for f in fields])

        if search and self.search_fields:
            search_keywords = search.split()
            filters = ' or '.join(
                '{} ILIKE  %s'.format(f)
                for f in self.search_fields for x in search_keywords
            )
            separator = 'WHERE' if 'WHERE' not in query_filters else 'AND'
            query_filters = '{query} {separator} {filters}'.format(
                query=query_filters, separator=separator, filters=filters
            )
            query_args += tuple(
                [
                    '%{}%'.format(kw) for kw in search_keywords
                    for x in self.search_fields
                ]
            )

        return query_filters, query_args

    @asyncio.coroutine
    def get_count(self, conditions=None, search=None):
        query_filters, query_args = \
            self.get_list_query_filters(conditions, search)
        count_query = self.get_count_query()
        if asyncio.iscoroutine(count_query):
            count_query = yield from count_query

        query = ' '.join([count_query, query_filters])

        with (yield from self.get_cursor()) as cur:
            yield from cur.execute(query, query_args)
            return (yield from cur.fetchone())[0]

    def index(self):
        index = yield from self.do_index()
        return self.response(index)

    @property
    def offset(self):
        return int(self.request.GET.get('offset') or 0)

    @property
    def limit(self):
        from_url = self.request.GET.get('limit')
        from_env = int(os.environ.get('PAGE_LIMIT') or 20)
        return int(from_url or from_env)

    @property
    def prev_offset(self):
        if self.limit <= 0:
            return 0

        offset = self.offset - self.limit
        return offset if offset > 0 else 0

    @classmethod
    def relation(cls, resource, **kwargs):
        base = os.getenv('BASE_URL', 'http://localhost:8000')
        return dict(
            tipo='relation',
            resource='{}/{}'.format(base, resource),
            **kwargs
        )

    @property
    def next_offset(self):
        if self.limit <= 0:
            return 0

        return self.offset + self.limit

    def _build_url(self, args):
        kwarg = self.default_kwargs_for_urls()
        return '{}?{}'.format(
            self.get_index_url(**kwarg),
            '&'.join(
                ['{}={}'.format(k, v) for k, v in args.items()]
            )
        )

    def next_url(self, conditions, count, search):

        if self.next_offset <= self.offset or self.next_offset >= count:
            return None

        args = conditions.copy()
        if search:
            args.update(dict(search=quote_plus(search)))

        args.update(
            dict(
                offset=self.next_offset,
                limit=self.limit
            )
        )
        return self._build_url(args)

    def prev_url(self, conditions, search):
        if self.prev_offset >= self.offset:
            return None

        args = conditions.copy()
        if search:
            args.update(dict(search=quote_plus(search)))

        args.update(
            dict(
                offset=self.prev_offset,
                limit=self.limit
            )
        )
        return self._build_url(args)

    def set_limit(self, query):
        if self.offset > 0:
            query = '{query} OFFSET {offset}'.format(
                query=query, offset=self.offset
            )
        return query

    def set_offset(self, query):
        if self.limit > 0:
            query = '{query} LIMIT {limit}'.format(
                query=query, limit=self.limit
            )

        return query

    def validate_allowed_order_by(self, f):
        if f not in self.allow_order_by:
            raise HTTPBadRequest(
                body=self.error_response(
                    'Order by "{field_name}" is not allowed'.format(
                        field_name=f
                    )
                )
            )

    def get_order_by(self):
        order_by_fields = []
        if 'order_by' in self.request.GET:
            order_by = self.request.GET['order_by']
            order_by = order_by.split(',')
            for x in order_by:
                if x.startswith('-'):
                    self.validate_allowed_order_by(x[1:])
                    order_by_fields.append(x[1:]+'{}'.format(' Desc'))
                else:
                    self.validate_allowed_order_by(x)
                    order_by_fields.append(x+'{}'.format(' Asc'))
            for a in self.order_by.split(','):
                if a not in order_by_fields:
                    order_by_fields.append(a)
            return ','.join(order_by_fields)
        else:
            return self.order_by

    def do_index(self, conditions=None):
        conditions = conditions or {}
        search = self.request.GET.get('search')
        query_filters, query_args = \
            self.get_list_query_filters(conditions, search)
        order_by = 'order by {}'.format(self.get_order_by())
        get_list_query = self.get_list_query()
        if asyncio.iscoroutine(get_list_query):
            get_list_query = yield from get_list_query
        query = ' '.join([get_list_query, query_filters, order_by])
        query = self.set_offset(self.set_limit(query))
        count = yield from self.get_count(conditions, search)
        response = dict(
            self=self.get_self_url(),
            data=dict(
                offset=self.offset,
                limit=self.limit,
                next=self.next_url(conditions, count, search),
                prev=self.prev_url(conditions, search),
                count=count
            ),
            index=[]
        )
        pool = yield from self.get_pool()
        with (yield from pool.cursor()) as cur:
            yield from cur.execute(query, query_args)
            for row in (yield from cur.fetchall()):
                row = self.before_serialization(row)
                if asyncio.iscoroutine(row):  # pragma: no cover
                    row = yield from row
                obj = self.serialize_object(row)
                if asyncio.iscoroutine(obj):  # pragma: no cover
                    obj = yield from obj
                obj = self.after_serialization(obj)
                if asyncio.iscoroutine(obj):
                    obj = yield from obj

                response['index'].append(obj)
        response['data']['length'] = len(response['index'])
        return response

    def serialize_list_object(self, row):
        return self.serialize_object(row)

    def serialize_object(self, row):  # pragma: no cover
        return row

    def before_serialization(self, row):
        return row

    def after_serialization(self, obj):
        return obj

    def show(self, id, **kwargs):
        pool = yield from self.get_pool()

        with (yield from pool.cursor()) as cur:
            yield from cur.execute(
                '{query} where {id_column} = %s'.format(
                    query=self.get_object_query(), id_column=self.id_column
                ), (id,)
            )
            record = yield from cur.fetchone()

            if record is None:
                raise HTTPNotFound()

            record = self.before_serialization(record)
            if asyncio.iscoroutine(record):
                record = yield from record
            obj = self.serialize_object(record)
            obj = self.after_serialization(obj)
            if asyncio.iscoroutine(obj):
                obj = yield from obj

            return self.response(obj)

    def get_table_name(self):
        if self.table_name:  # pragma: no cover
            return self.table_name
        return self.get_resource_name()

    @asyncio.coroutine
    def before_update(self, cursor):  # pragma: no cover
        return cursor

    @asyncio.coroutine
    def after_update(self, cursor):  # pragma: no cover
        return cursor

    def prepare_update(self, data):  # pragma: no cover
        return data

    def prepare_insert(self, data):  # pragma: no cover
        return data

    @asyncio.coroutine
    def before_insert(self, cursor):  # pragma: no cover
        return cursor

    @asyncio.coroutine
    def after_insert(self, cursor, id):  # pragma: no cover
        return cursor

    def get_allowed_fields(self):
        return self.allowed_fields

    def get_required_fields(self):
        return self.required_fields

    def error_response(self, message, **kwargs):
        kwargs['message'] = str(message)
        return json.dumps(kwargs, indent=4).encode('utf-8')

    def validate_allowed_fields(self, data):
        for f in data.keys():
            if f not in self.get_allowed_fields():
                raise HTTPBadRequest(
                    body=self.error_response(
                        'Field "{field_name}" is not allowed'.format(
                            field_name=f
                        )
                    )
                )

    def validate_required_fields(self, data):
        id = self.request.match_info.get('id')
        a = {}
        required = self.get_required_fields()
        if asyncio.iscoroutine(required):
            required = yield from self.get_required_fields()

        for f in required:
            if id:
                a[f] = data.get(f, " ")
                print(data.get(f, " "))
                if f in data:
                    if len(str(a.get(f)).strip()) == 0 or a.get(f) is None:
                        raise HTTPBadRequest(
                            body=self.error_response(
                                'Field "{field_name}" is required'.format(
                                    field_name=f
                                )
                            ),
                            headers=[
                                ['Access-Control-Allow-Origin', '*'],
                            ]
                        )

            else:
                if f not in data.keys():
                    raise HTTPBadRequest(
                        body=self.error_response(
                            'Field "{field_name}" is required'.format(
                                field_name=f
                            )
                        ),
                        headers=[
                            ['Access-Control-Allow-Origin', '*'],
                        ]
                    )

    def update(self, id, **kwargs):
        data = yield from self.request.json()

        result_allowed = self.validate_allowed_fields(data)
        if asyncio.iscoroutine(result_allowed):  # pragma: no cover
            yield from result_allowed

        result_required = self.validate_required_fields(data)
        if asyncio.iscoroutine(result_required):  # pragma: no cover
            yield from result_required

        data = self.prepare_update(data)
        if asyncio.iscoroutine(data):  # pragma: no cover
            data = yield from data

        updated_fields = data.keys()

        pool = yield from self.get_pool()
        with(yield from pool.cursor()) as cur:
            yield from self.before_update(cur)
            query = 'update {table} set {fields} where {id_column}=%s'.format(
                table=self.get_table_name(),
                fields=','.join(['{}=%s'.format(x)for x in updated_fields]),
                id_column=self.id_column
            )
            try:
                yield from cur.execute(
                    query, tuple([data[f] for f in updated_fields]+[id])
                )
            except DatabaseError as e:
                raise HTTPConflict(
                    body=self.error_response(e)
                )
            yield from self.after_update(cur)

        return Response(status=204)

    def new(self, **kwargs):
        data = yield from self.request.json()

        result_allowed = self.validate_allowed_fields(data)
        if asyncio.iscoroutine(result_allowed):  # pragma: no cover
            yield from result_allowed

        result_required = self.validate_required_fields(data)
        if asyncio.iscoroutine(result_required):  # pragma: no cover
            yield from result_required

        data = self.prepare_insert(data)
        if asyncio.iscoroutine(data):  # pragma: no cover
            data = yield from data

        fields = data.keys()

        pool = yield from self.get_pool()
        with (yield from pool.cursor()) as cur:
            query = (
                'INSERT INTO {table} ({fields}) '
                'VALUES ({values}) '
                'returning {id_column}'
            ).format(
                table=self.get_table_name(),
                fields=','.join(fields),
                values=','.join(['%s' for x in fields]),
                id_column=self.id_column
            )

            values = (data[x] for x in fields)

            yield from self.before_insert(cur)
            try:
                yield from cur.execute(query, tuple(values))
            except DatabaseError as e:
                raise HTTPConflict(
                    body=self.error_response(e)
                )
            record_id = (yield from cur.fetchone())[0]
            yield from self.after_insert(cur, record_id)

        return Response(
            status=201,
            headers=(('Location', self.get_object_url(record_id)),)
        )

    def destroy(self, **kwargs):
        pool = yield from self.get_pool()
        with(yield from pool.cursor()) as cur:
            query = 'DELETE FROM {table} where id={id_column}'.format(
                table=self.get_table_name(),
                id_column=kwargs['id']
            )
            try:
                yield from cur.execute(
                    query
                )
            except DatabaseError as e:
                raise HTTPConflict(
                    body=self.error_response(e)
                )

        return Response(status=200)
