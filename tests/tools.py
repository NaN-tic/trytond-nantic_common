import json
from types import SimpleNamespace

from proteus import Model
from sql import Table
from trytond.protocols.jsonrpc import JSONDecoder, JSONEncoder
from trytond.transaction import Transaction


class SetupCache:
    """Store fixture references in a table included in the test backup."""

    def __init__(self, config):
        self.config = config
        self.table = Table('test_setup_cache')

    def save(self, vars):
        rows = []
        for name, value in vars.__dict__.items():
            if name == 'config':
                continue
            if isinstance(value, Model):
                assert value.id >= 0, f'Unsaved setup record: {name}'
                rows.append((name, value.__class__.__name__, value.id, None))
            else:
                rows.append((name, None, None,
                    json.dumps(value, default=self._encode)))
        rows.append(('config', None, None, json.dumps({
            'user': self.config.user, 'context': self.config.context},
            default=self._encode)))
        with Transaction().start(self.config.database_name, 0) as transaction:
            cursor = transaction.connection.cursor()
            cursor.execute('CREATE TABLE test_setup_cache ('
                'name VARCHAR PRIMARY KEY, model VARCHAR, '
                'record_id INTEGER, value TEXT)')
            table = self.table
            cursor.execute(*table.insert(
                [table.name, table.model, table.record_id, table.value], rows))

    def load(self):
        with Transaction().start(
                self.config.database_name, 0, readonly=True) as transaction:
            cursor = transaction.connection.cursor()
            table = self.table
            cursor.execute(*table.select())
            references = cursor.fetchall()
        for row in references:
            if row[0] == 'config':
                config = json.loads(row[3], object_hook=self._decode)
                self.config.user = config['user']
                self.config._context = config['context']
        vars = SimpleNamespace(config=self.config)
        for row in references:
            name, model, record_id = row[:3]
            if name == 'config':
                continue
            if model:
                value = Model.get(model, config=self.config)(record_id)
            else:
                value = json.loads(row[3], object_hook=self._decode)
            setattr(vars, name, value)
        return vars

    @staticmethod
    def _encode(value):
        if isinstance(value, Model):
            assert value.id >= 0, 'Unsaved setup record'
            return {'__class__': 'setup_record',
                'model': value.__class__.__name__, 'id': value.id}
        return JSONEncoder().default(value)

    def _decode(self, value):
        if value.get('__class__') == 'setup_record':
            return Model.get(value['model'], config=self.config)(value['id'])
        return JSONDecoder()(value)

