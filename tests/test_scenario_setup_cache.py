import datetime
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from proteus import Model
from trytond.modules.nantic_common.tests.tools import SetupCache
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class TestSetupCache(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):
        def initialize(config):
            User = Model.get('res.user', config=config)
            user = User(name='Setup User', login='setup-cache')
            user.save()
            config._context['setup_cache_marker'] = 'restored'
            SetupCache(config).save(SimpleNamespace(
                config=config, user=user,
                users={'admin': user}, records=[user],
                today=datetime.date(2026, 10, 13),
                amount=Decimal('12.34'), workbook=b'fixture\x00data',
                optional=None, enabled=True, counter=0))

        config = activate_modules('nantic_common', initialize)
        original = SetupCache(config).load()
        original_name = original.user.name
        original.user.name = 'Changed by a test'
        original.user.save()
        drop_db()

        with patch.object(SetupCache, 'save',
                side_effect=AssertionError('The fixture was rebuilt')):
            config = activate_modules('nantic_common', initialize)
            restored = SetupCache(config).load()
        self.assertEqual(restored.user.name, original_name)
        self.assertEqual(restored.user.id, original.user.id)
        self.assertIsNot(restored.user, original.user)
        self.assertEqual(restored.users['admin'], restored.user)
        self.assertEqual(restored.records, [restored.user])
        self.assertIs(restored.records[0]._config, config)
        self.assertEqual(restored.today, datetime.date(2026, 10, 13))
        self.assertEqual(restored.amount, Decimal('12.34'))
        self.assertEqual(restored.workbook, b'fixture\x00data')
        self.assertIsNone(restored.optional)
        self.assertIs(restored.enabled, True)
        self.assertEqual(restored.counter, 0)
        self.assertEqual(config.context['setup_cache_marker'], 'restored')
