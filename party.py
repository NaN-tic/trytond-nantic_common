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


class ContactMechanism(metaclass=PoolMeta):
    __name__ = 'party.contact_mechanism'

    def format_value(self, value=None, type_=None):
        from trytond.modules.party.contact_mechanism import _PHONE_TYPES

        # Preserve the entered phone format.
        if type_ in _PHONE_TYPES:
            return value
        return super().format_value(value=value, type_=type_)

    def format_value_compact(self, value=None, type_=None):
        from trytond.modules.party.contact_mechanism import _PHONE_TYPES

        # Preserve the entered phone format in the compact field as well.
        if type_ in _PHONE_TYPES:
            return value
        return super().format_value_compact(value=value, type_=type_)

    @classmethod
    def check_valid_phonenumber(cls, mechanisms, field_names=None):
        # Intentionally skip super() to accept phone numbers even when the
        # optional phonenumbers library considers them invalid.
        return


class PartyPurchaseInvoiceLineStandalone(metaclass=PoolMeta):
    __name__ = 'party.party.purchase_invoice_line_standalone'

    @classmethod
    def default_purchase_invoice_line_standalone(cls):
        return True
