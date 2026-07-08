from trytond.pool import PoolMeta
from trytond.tools import is_full_text, lstrip_wildcard


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    @classmethod
    def search_rec_name(cls, name, clause):
        # Override default search_rec_name to not strip the wildcard at the
        # beginning of the operand when searching by code
        _, operator, operand, *extra = clause
        domain = super().search_rec_name(name, clause)
        if operator.endswith('like') and is_full_text(operand):
            domain += [
                ('code', operator, '%' + lstrip_wildcard(operand), *extra),
                ('products.code', operator, '%' + lstrip_wildcard(operand),
                    *extra),
                ]
        return domain


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'

    @classmethod
    def search_rec_name(cls, name, clause):
        # Override default search_rec_name to not strip the wildcard at the
        # beginning of the operand when searching by code
        _, operator, operand, *extra = clause
        domain = super().search_rec_name(name, clause)
        if operator.endswith('like') and is_full_text(operand):
            domain += [
                ('code', operator, '%' + lstrip_wildcard(operand), *extra),
                ('template.code', operator, '%' + lstrip_wildcard(operand),
                    *extra),
                ]
        return domain
