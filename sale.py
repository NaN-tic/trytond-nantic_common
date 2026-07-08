from trytond.pool import PoolMeta


class ConfigurationSaleMethod(metaclass=PoolMeta):
    __name__ = 'sale.configuration.sale_method'

    @classmethod
    def default_sale_invoice_method(cls):
        return 'fulfillment'
