# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction


class NanticCommonTestCase(ModuleTestCase):
    'Test Nantic Common module'
    module = 'nantic_common'
    extras = ['account_invoice', 'account_product', 'party',
        'party_relationship', 'product', 'purchase', 'purchase_request',
        'purchase_invoice_line_standalone', 'sale', 'sale_opportunity']

    @with_transaction()
    def test_manual_invoice_group_exists(self):
        Group = Pool().get('res.group')

        groups = Group.search([('name', '=', 'Manual Invoice Allowed')], limit=1)

        self.assertEqual(len(groups), 1)

    @with_transaction()
    def test_party_identifier_type(self):
        pool = Pool()
        Configuration = pool.get('party.configuration')
        Party = pool.get('party.party')

        self.assertIn(('vat-no-validation',
                'Foreign Identifier Without Validation'),
            Configuration.identifier_types.selection)
        self.assertIn('vat-no-validation', Party.tax_identifier_types())

    @with_transaction()
    def test_default_invoice_methods(self):
        pool = Pool()
        PurchaseMethod = pool.get('purchase.configuration.purchase_method')
        SaleMethod = pool.get('sale.configuration.sale_method')

        self.assertEqual(
            PurchaseMethod.default_purchase_invoice_method(), 'fulfillment')
        self.assertEqual(
            SaleMethod.default_sale_invoice_method(), 'fulfillment')
        self.assertEqual(pool.get('ir.sequence').default_padding(), 6)
        self.assertEqual(pool.get('ir.sequence.strict').default_padding(), 6)

    @with_transaction()
    def test_search_rec_name_overrides(self):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        ModelField = pool.get('ir.model.field')
        Opportunity = pool.get('sale.opportunity')
        Product = pool.get('product.product')
        Queue = pool.get('ir.queue')

        invoice_domain = Invoice.search_rec_name(
            'test', ('rec_name', 'ilike', '%test%'))
        queue_domain = Queue.search_rec_name(
            'test', ('rec_name', 'ilike', '%test%'))
        opportunity_domain = Opportunity.search_rec_name(
            'test', ('rec_name', 'ilike', '%test%'))
        product_domain = Product.search_rec_name(
            'test', ('rec_name', 'ilike', '%ABC'))

        self.assertIn('context', ModelField._fields)
        self.assertIn('instances', Queue._fields)
        self.assertIn(('party.rec_name', 'ilike', '%test%'), invoice_domain)
        self.assertIn(('model', 'ilike', '%test%'), queue_domain)
        self.assertIn(('party.rec_name', 'ilike', '%test%'),
            opportunity_domain)
        self.assertIn(('description', 'ilike', '%test%'), opportunity_domain)
        self.assertIn(('code', 'ilike', '%ABC'), product_domain)


del ModuleTestCase
