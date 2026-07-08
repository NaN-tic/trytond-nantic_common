from trytond.pool import PoolMeta


class Opportunity(metaclass=PoolMeta):
    __name__ = 'sale.opportunity'

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = super().search_rec_name(name, clause)
        domain.append(('party.rec_name',) + tuple(clause[1:]))
        domain.append(('description',) + tuple(clause[1:]))
        return domain
