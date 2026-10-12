from types import SimpleNamespace

from proteus import Model
from sql import Table
from trytond.transaction import Transaction


class SetupCache:
    """Store fixture references in a table included in the test backup."""

    def __init__(self, config):
        self.config = config
        self.table = Table('test_setup_cache')

    def save(self, vars):
        with Transaction().start(self.config.database_name, 0) as transaction:
            cursor = transaction.connection.cursor()
            cursor.execute('CREATE TABLE test_setup_cache ('
                'name VARCHAR PRIMARY KEY, model VARCHAR NOT NULL, '
                'record_id INTEGER NOT NULL)')
            table = self.table
            cursor.execute(*table.insert(
                [table.name, table.model, table.record_id],
                [(name, record.__class__.__name__, record.id)
                    for name, record in vars.__dict__.items()
                    if name != 'config']))

    def load(self):
        with Transaction().start(
                self.config.database_name, 0, readonly=True) as transaction:
            cursor = transaction.connection.cursor()
            table = self.table
            cursor.execute(*table.select(
                table.name, table.model, table.record_id))
            references = cursor.fetchall()
        vars = SimpleNamespace(config=self.config)
        for name, model, record_id in references:
            setattr(vars, name, Model.get(model, config=self.config)(record_id))
        return vars

