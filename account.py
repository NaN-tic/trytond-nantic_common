from sql.aggregate import Max
from sql.conditionals import Coalesce
from trytond.model import ModelSQL
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction


class Cron(metaclass=PoolMeta):
    __name__ = 'ir.cron'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.method.selection.extend([
                ('nantic.account.update|update',
                    "Update Account Template Records"),
                ])


class NanticAccountUpdate(ModelSQL):
    'NaN-tic Account Update'
    __name__ = 'nantic.account.update'

    @classmethod
    def update(cls):
        pool = Pool()
        Company = pool.get('company.company')
        Config = pool.get('account.configuration')
        Account = pool.get('account.account')
        AccountTemplate = pool.get('account.account.template')
        UpdateChart = pool.get('account.update_chart', type='wizard')

        account_ = Account.__table__()
        cursor = Transaction().connection.cursor()

        def newest(model):
            try:
                Model = pool.get(model)
            except KeyError:
                return
            table = Model.__table__()
            cursor.execute(*table.select(Max(
                Coalesce(table.write_date, table.create_date))))
            max_date = cursor.fetchone()
            if not max_date:
                return
            return max_date[0]

        def _code_digits(template, config_digits):
            code = template.code
            if template.type and template.parent:
                digits = int(config_digits - len(code))
                if '%' in code:
                    return code.replace(
                        '%', '0' * (digits + 1))
                return code + '0' * digits
            return code

        models = (
            'account.account.type.template',
            'account.account.template',
            'account.account.template-account.tax.template',
            'account.tax.code.template',
            'account.tax.code.line.template',
            'account.tax.template', 'account.tax.rule.template',
            'account.tax.rule.line.template',
            'aeat.303.mapping-account.tax.code.template',
            'aeat.349.type-account.tax.template',
            'aeat.111.mapping-account.tax.code.template',
            'aeat.115.mapping-account.tax.code.template',
            )

        dates = [newest(m) for m in models]
        max_date = max(x for x in dates if x)
        if not max_date:
            return

        update_date = cls.search([], order=[('create_date', 'DESC')],
            limit=1)
        if update_date and update_date[0].create_date >= max_date:
            return

        templates = None
        if hasattr(Config, 'default_account_code_digits'):
            templates = AccountTemplate.search([('code', '!=', None)])

        for company in Company.search([]):
            with Transaction().set_context(company=company.id):
                roots = Account.search([
                        ('parent', '=', None),
                        ('template', '!=', None),
                        ('company', '=', company.id),
                        ], limit=1)
                if not roots:
                    continue

                config = Config(1)
                if templates and config.default_account_code_digits is not None:
                    digits = config.default_account_code_digits

                    template_codes = dict((_code_digits(t, digits), t)
                        for t in templates if (t.type and t.parent))
                    accounts = Account.search([
                            ('code', 'in', template_codes.keys()),
                            ('template', '=', None),
                            ('company', '=', company.id),
                            ])
                    for account in accounts:
                        template = template_codes.get(account.code)
                        if not template:
                            continue

                        query = account_.update(
                            columns=[account_.template, account_.template_override],
                            values=[template.id, True],
                            where=(account_.id == account.id))
                        cursor.execute(*query)

                root, = roots

                session_id, _, _ = UpdateChart.create()
                update_chart = UpdateChart(session_id)
                if hasattr(config, 'default_account_code_digits'):
                    update_chart.start.account_code_digits = (
                        config.default_account_code_digits)
                update_chart.start.account = root
                update_chart.transition_update()

        cls.delete(cls.search([]))
        nantic_account_update = cls()
        nantic_account_update.save()
