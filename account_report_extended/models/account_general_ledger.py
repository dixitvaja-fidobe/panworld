import json
from collections import defaultdict
from odoo import models, fields, _
from odoo.tools import SQL

class AccountGeneralLedgerReportHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    def _report_custom_engine_general_ledger(self, expressions, options, date_scope, current_groupby, next_groupby, offset=0, limit=None, warnings=None):
        def get_grouping_key(row, groupby):
            if groupby == 'id_with_accumulated_balance':
                if not row['id']:
                    return f"balance_line_{row['account_id']}"
                else:
                    return json.dumps([fields.Date.to_string(row['date']), row['id']])
            return row[groupby] if groupby else None

        report = self.env['account.report'].browse(options['report_id'])
        options_date_from = fields.Date.from_string(options['date']['date_from'])
        current_fiscalyear_date_from = self.env.company.compute_fiscalyear_dates(options_date_from)['date_from']

        # We want to exclude move lines from expense and income accounts before the fiscal year for every groupby under account_id
        additional_domain = [
            '|',
            ('account_id.include_initial_balance', '=', True),
            ('date', '>=', current_fiscalyear_date_from),
        ]

        report_query = report._get_report_query(options, 'from_beginning', additional_domain)

        if options.get('export_mode') == 'print' and options.get('filter_search_bar') and current_groupby not in ('id_with_accumulated_balance', 'id'):
            search_bar_sql = SQL(
                """
                AND result_account.id = ANY(%(search_bar_account_query)s)
                """,
                search_bar_account_query=self.env['account.account']._search([
                    ('display_name', 'ilike', options.get('filter_search_bar')),
                    *self.env['account.account']._check_company_domain(self.env['account.report'].get_report_company_ids(options)),
                ]).select(SQL.identifier('id'))
            )
        else:
            search_bar_sql = SQL()

        additional_select = SQL("")
        groupby = []
        if current_groupby == 'id_with_accumulated_balance':
            account_code_select = self.env['account.account']._field_to_sql('result_account', 'code', report_query)
            account_name_select = self.env['account.account']._field_to_sql('result_account', 'name')
            additional_select = SQL("""
                CASE
                    WHEN account_move_line.date >= %(date)s THEN account_move_line.id
                    ELSE NULL
                END AS id,
                CASE
                    WHEN account_move_line.date >= %(date)s THEN account_move_line.date
                    ELSE NULL
                END AS date,
                MIN(move.name::text) AS move_name,

                SUM(account_move_line.amount_currency) AS amount_currency,
                MIN(partner.name::text) AS partner_name,
                MIN(account_move_line.currency_id) AS currency_id,
                MIN(result_account.id) AS account_id,

                MIN(account_move_line.name::text) AS line_name,
                MIN((%(account_name_select)s)::text) AS account_name,
                MIN((%(account_code_select)s)::text) AS account_code,
                """,
                date=fields.Date.from_string(options['date']['date_from']),
                account_name_select=account_name_select,
                account_code_select=account_code_select,
            )
            groupby = [SQL("1"), SQL("2"), SQL("account_id")]
        elif current_groupby == 'account_id':
            additional_select = SQL("""
                result_account.id AS account_id,
                result_account.account_type AS account_type,
                SUM(account_move_line.amount_currency) AS amount_currency,
                result_account.currency_id AS currency_id,
            """)
            groupby = [SQL("result_account.id"), SQL("result_account.currency_id")]
        elif current_groupby:
            additional_select = SQL("%s,", self.env['account.move.line']._field_to_sql('account_move_line', current_groupby, report_query))
            groupby = [SQL("%s", self.env['account.move.line']._field_to_sql('account_move_line', current_groupby, report_query))]

        query = SQL(
            """
            SELECT
                %(additional_select)s
                COALESCE(SUM(%(select_debit)s), 0.0) AS debit,
                COALESCE(SUM(%(select_credit)s), 0.0) AS credit,
                COALESCE(SUM(%(select_balance)s), 0.0) AS balance
            FROM %(from_clause)s

            LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
            JOIN account_account account ON account.id = account_move_line.account_id
            JOIN account_account result_account ON result_account.id = account_move_line.account_id

            JOIN account_move move ON move.id = account_move_line.move_id
            %(currency_table_join)s

            WHERE %(where_clause)s
            %(search_bar_sql)s

            %(additional_groupby)s
            %(orderby_clause)s

            %(offset_clause)s
            LIMIT %(limit)s
            """,
            additional_select=additional_select,
            select_balance=report._currency_table_apply_rate(SQL("account_move_line.balance")),
            select_debit=report._currency_table_apply_rate(SQL("account_move_line.debit")),
            select_credit=report._currency_table_apply_rate(SQL("account_move_line.credit")),
            from_clause=report_query.from_clause,
            currency_table_join=report._currency_table_aml_join(options),
            where_clause=report_query.where_clause,
            search_bar_sql=search_bar_sql,
            additional_groupby=SQL("GROUP BY %s", SQL(",").join(groupby)) if groupby else SQL(),
            orderby_clause=SQL("ORDER BY 2 NULLS FIRST, move_name, 1 NULLS FIRST") if current_groupby == 'id_with_accumulated_balance' else SQL(),
            offset_clause=SQL("OFFSET %s", offset) if offset else SQL(),
            limit=limit
        )

        rows_by_key = defaultdict(lambda: {
            'date': None,
            'partner_name': None,
            'amount_currency': None,
            'currency_id': self.env.company.currency_id.id,
            'debit': 0,
            'credit': 0,
            'balance': 0,
            'has_sublines': True,
        })

        for row in self.env.execute_query_dict(query):
            aml_key = get_grouping_key(row, current_groupby)

            if aml_key not in rows_by_key:
                rows_by_key[aml_key].update({
                    'debit': row['debit'],
                    'credit': row['credit'],
                    'balance': row['balance'],
                })

                if current_groupby == 'id_with_accumulated_balance':
                    rows_by_key[aml_key]['has_sublines'] = False
                    rows_by_key[aml_key]['account_id'] = row['account_id']  # Needed for batching

                    if 'balance_line' not in aml_key:
                        rows_by_key[aml_key]['date'] = row['date']
                        rows_by_key[aml_key]['partner_name'] = row['partner_name']
                        rows_by_key[aml_key]['line_name'] = row['line_name']
                        rows_by_key[aml_key]['account_code'] = row['account_code']
                        rows_by_key[aml_key]['account_name'] = row['account_name']
                        rows_by_key[aml_key]['move_name'] = row['move_name']
                    if row['currency_id'] != self.env.company.currency_id.id:
                        rows_by_key[aml_key]['amount_currency'] = row['amount_currency']
                        rows_by_key[aml_key]['currency_id'] = row['currency_id']
                elif current_groupby == 'account_id':
                    rows_by_key[aml_key]['has_sublines'] = True
                    if row.get('currency_id'):
                        rows_by_key[aml_key]['amount_currency'] = row['amount_currency']
                        rows_by_key[aml_key]['currency_id'] = row['currency_id']
            else:
                rows_by_key[aml_key]['debit'] += row['debit']
                rows_by_key[aml_key]['credit'] += row['credit']
                rows_by_key[aml_key]['balance'] += row['balance']
                if row.get('currency_id'):
                    rows_by_key[aml_key]['currency_id'] += row['currency_id']

        if not current_groupby:
            return rows_by_key[None]  # None is the key for total line as there is no groupby

        return [(key, entry) for key, entry in rows_by_key.items()]
