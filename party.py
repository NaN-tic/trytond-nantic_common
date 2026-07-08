# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta


class Configuration(metaclass=PoolMeta):
    __name__ = 'party.configuration'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.identifier_types.selection += [
            ('vat-no-validation',
                'Foreign Identifier Without Validation'),
            ]


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    @classmethod
    def tax_identifier_types(cls):
        return super().tax_identifier_types() + [
            'vat-no-validation']


class PartyPurchaseInvoiceLineStandalone(metaclass=PoolMeta):
    __name__ = 'party.party.purchase_invoice_line_standalone'

    @classmethod
    def default_purchase_invoice_line_standalone(cls):
        return True
