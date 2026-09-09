# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.cache import BaseCache
from trytond.pool import Pool

from . import account
from . import account_product
from . import invoice
from . import ir
from . import opportunity
from . import party
from . import product
from . import purchase
from . import sale

BaseCache.context_ignored_keys.add('smile')


def register():
    Pool.register(
        ir.Sequence,
        ir.SequenceStrict,
        ir.ModelField,
        ir.Queue,
        module='nantic_common', type_='model')
    Pool.register(
        account.Cron,
        account.NanticAccountUpdate,
        depends=['account'],
        module='nantic_common', type_='model')
    Pool.register(
        invoice.Invoice,
        depends=['account_invoice'],
        module='nantic_common', type_='model')
    Pool.register(
        account_product.Template,
        depends=['account_product'],
        module='nantic_common', type_='model')
    Pool.register(
        party.Configuration,
        party.Party,
        party.ContactMechanism,
        depends=['party'],
        module='nantic_common', type_='model')
    Pool.register(
        product.Template,
        product.Product,
        depends=['product'],
        module='nantic_common', type_='model')
    Pool.register(
        purchase.ConfigurationPurchaseMethod,
        depends=['purchase'],
        module='nantic_common', type_='model')
    Pool.register(
        party.PartyPurchaseInvoiceLineStandalone,
        depends=['purchase_invoice_line_standalone'],
        module='nantic_common', type_='model')
    Pool.register(
        sale.ConfigurationSaleMethod,
        depends=['sale'],
        module='nantic_common', type_='model')
    Pool.register(
        opportunity.Opportunity,
        depends=['sale_opportunity'],
        module='nantic_common', type_='model')
