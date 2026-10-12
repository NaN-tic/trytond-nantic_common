import datetime
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from proteus import Model
from trytond.modules.company.tests.tools import create_company, get_company
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
            create_company(config=config)
            company = get_company(config=config)
            config._context['setup_cache_marker'] = 'restored'
            SetupCache(config).save(SimpleNamespace(
                config=config, company=company,
                accounts={'party': company.party},
                records=[company, company.party],
                today=datetime.date(2026, 10, 13),
                amount=Decimal('12.34'), workbook=b'fixture\x00data',
                optional=None, enabled=True, counter=0))

        config = activate_modules(['nantic_common', 'company'], initialize)
        original = SetupCache(config).load()
        original_name = original.company.party.name
        original.company.party.name = 'Changed by a test'
        original.company.party.save()
        drop_db()

        with patch.object(SetupCache, 'save',
                side_effect=AssertionError('The fixture was rebuilt')):
            config = activate_modules(['nantic_common', 'company'], initialize)
            restored = SetupCache(config).load()
        self.assertEqual(restored.company.party.name, original_name)
        self.assertEqual(restored.company.id, original.company.id)
        self.assertIsNot(restored.company, original.company)
        self.assertEqual(restored.accounts['party'], restored.company.party)
        self.assertEqual(restored.records, [restored.company,
            restored.company.party])
        self.assertIs(restored.records[0]._config, config)
        self.assertEqual(restored.today, datetime.date(2026, 10, 13))
        self.assertEqual(restored.amount, Decimal('12.34'))
        self.assertEqual(restored.workbook, b'fixture\x00data')
        self.assertIsNone(restored.optional)
        self.assertIs(restored.enabled, True)
        self.assertEqual(restored.counter, 0)
        self.assertEqual(config.context['setup_cache_marker'], 'restored')
        self.assertEqual(Model.get('company.company', config=config).find([]),
            [restored.company])
