from trytond.pool import PoolMeta
from trytond.transaction import Transaction


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = super().search_rec_name(name, clause)
        domain.append(('party.rec_name',) + tuple(clause[1:]))
        return domain

    def get_move(self):
        with Transaction().set_context(_skip_warnings=True):
            return super().get_move()

    @property
    def invoice_report_versioned(self):
        if Transaction().context.get('output_format') == 'html':
            return False
        return super().invoice_report_versioned
