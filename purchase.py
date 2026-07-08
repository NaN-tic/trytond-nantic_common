from trytond.pool import PoolMeta


class ConfigurationPurchaseMethod(metaclass=PoolMeta):
    __name__ = 'purchase.configuration.purchase_method'

    @classmethod
    def default_purchase_invoice_method(cls):
        return 'fulfillment'
