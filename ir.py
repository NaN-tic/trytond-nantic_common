import json
import re
from datetime import date

from sql import Cast, Literal
from sql.functions import Function
from trytond.config import config
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval
from trytond.transaction import Transaction

WORKER_QUEUES = config.get('nantic_connection', 'worker_queues', default='')
WORKER_DEFAULT_QUEUE = config.get('nantic_connection',
    'worker_default_queue', default='')
queues = WORKER_QUEUES.split('|')
QUEUE_NAME_RULES = {}
for queue in queues:
    queue_params = [x.strip() for x in queue.split(':')]
    if len(queue_params) == 3:
        model, method, queue_name = queue_params
        QUEUE_NAME_RULES[(model, method)] = queue_name


class Replace(Function):
    __slots__ = ()
    _function = 'REPLACE'


class SequenceMixin:
    __slots__ = ()

    @staticmethod
    def default_padding():
        return 6


class Sequence(SequenceMixin, metaclass=PoolMeta):
    __name__ = 'ir.sequence'


class SequenceStrict(SequenceMixin, metaclass=PoolMeta):
    __name__ = 'ir.sequence.strict'


class ModelField(metaclass=PoolMeta):
    __name__ = 'ir.model.field'
    context = fields.Function(fields.Char('Context', readonly=True),
            'get_field_attribute')
    domain = fields.Function(fields.Char('Domain', readonly=True),
            'get_field_attribute')
    is_function = fields.Function(fields.Boolean('Is Function'),
            'get_field_attribute')
    searcher = fields.Function(fields.Boolean('Has Searcher', states={
            'invisible': Bool(Eval('is_function')) == False,
            }), 'get_field_attribute')
    has_setter = fields.Function(fields.Boolean('Has Setter', states={
            'invisible': Bool(Eval('is_function')) == False,
            }), 'get_field_attribute')
    readonly_state = fields.Function(fields.Char('Read Only States',
                readonly=True), 'get_field_attribute')
    required_state = fields.Function(fields.Char('Required States',
                readonly=True), 'get_field_attribute')
    invisible_state = fields.Function(fields.Char('Invisible States',
                readonly=True), 'get_field_attribute')

    def get_field_attribute(self, name):
        pool = Pool()
        try:
            Model = pool.get(self.model)
        except KeyError:
            return None

        try:
            field = Model._fields.get(self.name)
            if not field:
                return None

            is_function = isinstance(field, fields.Function)

            if name == 'is_function':
                val = is_function
            elif name == 'has_setter':
                val = bool(is_function and getattr(field, 'setter', None))
            elif name == 'searcher':
                val = bool(is_function and getattr(field, 'searcher', None))
            else:
                if name.endswith('state'):
                    key = name.split('_', 1)[0]
                    val = getattr(field, 'states', {}).get(key, None)
                else:
                    val = getattr(field, name, None)
        except Exception:
            return None

        if (val is None
                or (isinstance(val, dict) and not val)
                or (isinstance(val, list) and not val)):
            return None

        if name in ('is_function', 'has_setter', 'searcher'):
            return bool(val) if val is not None else None
        try:
            return json.dumps(val, default=str, ensure_ascii=False)
        except TypeError:
            return json.dumps(str(val), ensure_ascii=False)


class Queue(ModelView, metaclass=PoolMeta):
    __name__ = 'ir.queue'
    method = fields.Function(fields.Char('Method'), 'get_data',
        searcher='search_data')
    model = fields.Function(fields.Char('Model'), 'get_data',
        searcher='search_data')
    instances = fields.Function(fields.Char('Instances'), 'get_data',
        searcher='search_data')
    json = fields.Function(fields.Text('JSON'), 'get_json')

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('model',) + tuple(clause[1:]),
            ('method',) + tuple(clause[1:]),
            ('model',) + tuple(clause[1:]),
            ('method',) + tuple(clause[1:]),
            ]

    def get_json(self, name):
        def _custom_serializer(obj):
            if isinstance(obj, date):
                return obj.isoformat()

        return self.data and json.dumps(self.data, indent=4, sort_keys=True,
            default=_custom_serializer)

    def get_data(self, name):
        return self.data and str(self.data.get(name, ''))

    @classmethod
    def _instances_ids_from_value(cls, value):
        if isinstance(value, (list, tuple, set, frozenset)):
            values = value
        else:
            values = [value]

        ids = []
        for item in values:
            if isinstance(item, int):
                ids.append(item)
            elif item is not None:
                ids.extend(int(match) for match in re.findall(r'\d+', str(item)))
        return sorted(set(ids))

    @classmethod
    def _search_instances_query(cls, operator, value):
        table = cls.__table__()
        transaction = Transaction()
        database = transaction.database
        instance_ids = cls._instances_ids_from_value(value)
        positive = operator in {'=', 'in', 'like', 'ilike'}
        negative = operator in {'!=', 'not in', 'not like', 'not ilike'}
        if not (positive or negative):
            return None

        if not instance_ids:
            return None

        raw_column = table.data
        try:
            expression = Literal(False)
            for instance_id in instance_ids:
                expression |= (
                    database.json_contains(
                        raw_column, json.dumps({'instances': instance_id}))
                    | database.json_contains(
                        raw_column, json.dumps({'instances': [instance_id]})))
        except NotImplementedError:
            column = Replace(
                Cast(raw_column, database.sql_type('VARCHAR').base),
                ' ', '')
            expression = Literal(False)
            for instance_id in instance_ids:
                value = str(instance_id)
                expression |= (
                    column.like(f'%"instances":{value},%')
                    | column.like(f'%"instances":{value}}}%')
                    | column.like(f'%"instances":[{value}]%')
                    | column.like(f'%"instances":[{value},%')
                    | column.like('%"instances":[%,' + value + ',%')
                    | column.like('%"instances":[%,' + value + ']%'))

        if negative:
            expression = ~expression
        return table.select(table.id, where=expression)

    @classmethod
    def search_data(cls, name, clause):
        if not clause[2]:
            return []
        if name == 'instances':
            positive = clause[1] in {'=', 'in', 'like', 'ilike'}
            negative = clause[1] in {'!=', 'not in', 'not like', 'not ilike'}
            query = cls._search_instances_query(clause[1], clause[2])
            if query is not None:
                return [('id', 'in', query)]
            if positive:
                return [('id', 'in', [])]
            if negative:
                return []
            return [('id', 'in', [])]

        return [('data.%s' % name, clause[1], clause[2])]

    @classmethod
    def push(cls, name, data, scheduled_at=None, expected_at=None):
        rule_name = QUEUE_NAME_RULES.get(
            (data.get('model'), data.get('method')), None)
        if rule_name:
            name = rule_name
        if not rule_name and WORKER_DEFAULT_QUEUE:
            name = WORKER_DEFAULT_QUEUE
        if not name:
            name = 'default'
        return super().push(name, data, scheduled_at, expected_at)
