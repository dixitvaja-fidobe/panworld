# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import models, fields, api, _
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT, formatLang
from datetime import timedelta
from odoo.tools import SQL
from dateutil.relativedelta import relativedelta
from itertools import chain

class AccountAgedPartner(models.AbstractModel):
    _inherit = 'account.aged.partner.balance.report.handler'

    def _custom_options_initializer(self, report, options, previous_options):
        if report.custom_handler_model_name == 'account.aged.receivable.report.handler':
            invoice_date_column = "Invoice Date"
        elif report.custom_handler_model_name == 'account.aged.payable.report.handler':
            invoice_date_column = "Bill Date"
        options['columns'][0]['name'] = invoice_date_column
        super()._custom_options_initializer(report, options, previous_options=previous_options)
        hidden_columns = set()

        options['multi_currency'] = report.env.user.has_group('base.group_multi_currency')
        options['show_currency'] = options['multi_currency'] and (previous_options or {}).get('show_currency', False)
        options['no_xlsx_currency_code_columns'] = True
        if not options['show_currency']:
            hidden_columns.update(['amount_currency', 'currency'])

        options['show_account'] = (previous_options or {}).get('show_account', False)
        if not options['show_account']:
            hidden_columns.add('account_name')

        options['columns'] = [
            column for column in options['columns']
            if column['expression_label'] not in hidden_columns
        ]

        if report.custom_handler_model_name == 'account.aged.receivable.report.handler':
            col_group_key = next((col.get('column_group_key') for col in options['columns'] if col.get('column_group_key')), None)
            options['columns'].insert(1, {'name': 'CSO Ref', 'expression_label': 'tracking_ref', 'class': 'text-center', 'sortable': True, 'column_group_key': col_group_key, 'figure_type': 'string'})
            options['columns'].insert(2, {'name': 'Invoice Due Date', 'expression_label': 'invoice_date_due', 'class': 'date', 'sortable': True, 'column_group_key': col_group_key, 'figure_type': 'date'})
            options['columns'].insert(3, {'name': 'Sales Manager', 'expression_label': 'sales_manager_id', 'class': 'text-start', 'sortable': True, 'column_group_key': col_group_key, 'figure_type': 'string'})
            options['columns'].insert(4, {'name': 'Company', 'expression_label': 'company_id', 'class': 'text-start', 'sortable': True, 'column_group_key': col_group_key, 'figure_type': 'string'})
        elif report.custom_handler_model_name == 'account.aged.payable.report.handler':
            col_group_key = next((col.get('column_group_key') for col in options['columns'] if col.get('column_group_key')), None)
            options['columns'].insert(1, {'name': 'Bill Ref', 'expression_label': 'bill_ref', 'class': 'text-center', 'sortable': True, 'column_group_key': col_group_key, 'figure_type': 'string'})
            options['columns'].insert(2, {'name': 'Bill Due Date', 'expression_label': 'invoice_date_due', 'class': 'date', 'sortable': True, 'column_group_key': col_group_key, 'figure_type': 'date'})
            options['columns'].insert(3, {'name': 'Company', 'expression_label': 'company_id', 'class': 'text-start', 'sortable': True, 'column_group_key': col_group_key, 'figure_type': 'string'})

        default_order_column = {
            'expression_label': 'invoice_date',
            'direction': 'ASC',
        }

        options['order_column'] = previous_options.get('order_column') or default_order_column
        options['aging_based_on'] = previous_options.get('aging_based_on') or 'base_on_maturity_date'
        options['aging_interval'] = previous_options.get('aging_interval') or 30

        # Set aging column names
        interval = options['aging_interval']
        for column in options['columns']:
            if column['expression_label'].startswith('period'):
                period_number = int(column['expression_label'].replace('period', '')) - 1
                if 0 <= period_number < 4:
                    column['name'] = f'{interval * period_number + 1}-{interval * (period_number + 1)}'
        options['custom_display_config'] = {
            'css_custom_class': 'aged_partner_balance',
            'templates': {
                'AccountReportLineName': 'account_reports.AgedPartnerBalanceLineName',
            },
            'components': {
                'AccountReportFilters': 'AgedPartnerBalanceFilters',
            },
        }
        
    def _custom_line_postprocessor(self, report, options, lines):
        lines = super()._custom_line_postprocessor(report, options, lines)
        
        aml_ids = []
        # First pass: collect AML IDs
        for line in lines:
            model, model_id = report._get_model_info_from_id(line['id'])
            if model == 'account.move.line':
                aml_ids.append(model_id)

        aml_values = {}
        if aml_ids:
            amls = self.env['account.move.line'].search([('id', 'in', aml_ids)])
            aml_values = {
                aml.id: {
                    'invoice_date_due': aml.move_id.invoice_date_due,
                    'tracking_ref': aml.move_id.tracking_ref,
                    'sales_manager_id': aml.move_id.sales_manager_id.name,
                    'bill_ref': aml.move_id.ref,
                    'company_id': aml.company_id.name,
                }
                for aml in amls
                if aml.move_id.journal_id.type in ('sale', 'purchase')
            }

        # Columns to populate: (expression_label, dict_key, is_date)
        cols_to_process = [
            ('invoice_date_due', 'invoice_date_due', True),
            ('tracking_ref', 'tracking_ref', False),
            ('sales_manager_id', 'sales_manager_id', False),
            ('bill_ref', 'bill_ref', False),
            ('company_id', 'company_id', False),
        ]

        expected_len = len(options['columns'])

        # Calculate indices and sort by index to ensure correct insertion order
        cols_with_indices = []
        for item in cols_to_process:
            expr_label = item[0]
            col_index = next((i for i, col in enumerate(options['columns']) if col.get('expression_label') == expr_label), None)
            if col_index is not None:
                cols_with_indices.append((col_index, item))
        
        cols_with_indices.sort(key=lambda x: x[0])

        for col_index, (expr_label, key, is_date) in cols_with_indices:
            # Ensure every line has the column cell at col_index and set value
            for line in lines:
                model, model_id = report._get_model_info_from_id(line['id'])
                val = None
                if model == 'account.move.line':
                    val = aml_values.get(model_id, {}).get(key)

                # Ensure we have a default for formatted_name even if val is None or False
                formatted_name = format_date(self.env, val) if is_date and val else (str(val) if val else '')

                cell_val = {
                    'name': formatted_name,
                    'no_format': val if (is_date and val) else (formatted_name or ''),
                    'class': 'text-center' if (is_date or key == 'tracking_ref') else 'text-start',
                }
                if is_date:
                    cell_val['figure_type'] = 'date'

                current_len = len(line['columns'])
                
                if current_len == expected_len:
                    # Cell exists (placeholder), update it
                    line['columns'][col_index].update(cell_val)
                elif current_len < expected_len:
                    # Cell missing, insert it
                    # We assume the missing one is ours at col_index, provided we insert in order
                    if col_index <= current_len:
                         line['columns'].insert(col_index, cell_val)
                    else:
                         # Append if gap (should not happen if sorted and sequential)
                         line['columns'].append(cell_val)
                else:
                    # Should unlikely happen: more columns than options?
                    # Try safe update
                    if col_index < current_len:
                        line['columns'][col_index].update(cell_val)

        # Logic for Total Amount Currency if partner has single currency
        # Check for currency columns
        cols = options.get('columns', [])
        curr_col_idx = next((i for i, c in enumerate(cols) if c.get('expression_label') == 'currency'), None)
        amt_curr_col_idx = next((i for i, c in enumerate(cols) if c.get('expression_label') == 'amount_currency'), None)
        total_amt_curr_no_sym_col_idx = next((i for i, c in enumerate(cols) if c.get('expression_label') == 'amount_currency_no_symbol'), None)

        if curr_col_idx is not None and amt_curr_col_idx is not None:
            partner_indices = {}
            for i, line in enumerate(lines):
                 model, model_id = report._get_model_info_from_id(line['id'])
                 if model == 'res.partner':
                     partner_indices[model_id] = i
            
            if partner_indices:
                # Query open receivables
                account_type = 'asset_receivable'
                if report.custom_handler_model_name == 'account.aged.payable.report.handler':
                    account_type = 'liability_payable'

                domain = [
                    ('partner_id', 'in', list(partner_indices.keys())),
                    ('account_id.account_type', '=', account_type),
                    ('parent_state', '=', 'posted'),
                    ('date', '<=', options['date']['date_to']),
                    ('reconciled', '=', False)
                ]
                amls = self.env['account.move.line'].search(domain)
                
                partner_currency_map = {} # pid -> {curr_id: total}
                for aml in amls:
                    pid = aml.partner_id.id
                    cid = aml.currency_id.id
                    # Using amount_residual_currency for open amount
                    amt = aml.amount_residual_currency
                    
                    if pid not in partner_currency_map:
                        partner_currency_map[pid] = {}
                    if cid not in partner_currency_map[pid]:
                        partner_currency_map[pid][cid] = 0.0
                    partner_currency_map[pid][cid] += amt
                
                for pid, idx in partner_indices.items():
                    currencies = partner_currency_map.get(pid, {})
                    if len(currencies) == 1:
                        # Single currency found
                        currency_id, total_amt = list(currencies.items())[0]
                        currency = self.env['res.currency'].browse(currency_id)
                        
                        # Populate columns
                        # Ensure we don't crash if indices are out of bounds (though they shouldn't be if columns exist)
                        if idx < len(lines) and amt_curr_col_idx < len(lines[idx]['columns']) and curr_col_idx < len(lines[idx]['columns']):
                             lines[idx]['columns'][curr_col_idx]['name'] = currency.name
                             lines[idx]['columns'][amt_curr_col_idx]['name'] = formatLang(self.env, total_amt, currency_obj=currency)
                             lines[idx]['columns'][amt_curr_col_idx]['no_format'] = total_amt
                             if total_amt_curr_no_sym_col_idx is not None and total_amt_curr_no_sym_col_idx < len(lines[idx]['columns']):
                                 lines[idx]['columns'][total_amt_curr_no_sym_col_idx]['no_format'] = total_amt
                                 lines[idx]['columns'][total_amt_curr_no_sym_col_idx]['figure_type'] = 'float'
                                 lines[idx]['columns'][total_amt_curr_no_sym_col_idx]['class'] = 'number'
                                 if 'name' in lines[idx]['columns'][total_amt_curr_no_sym_col_idx]:
                                     del lines[idx]['columns'][total_amt_curr_no_sym_col_idx]['name']

        # Force right alignment and total styling for the custom currency column on all lines
        total_amt_curr_no_sym_col_idx = next((i for i, c in enumerate(cols) if c.get('expression_label') == 'amount_currency_no_symbol'), None)
        if total_amt_curr_no_sym_col_idx is not None:
            for line in lines:
                if total_amt_curr_no_sym_col_idx < len(line.get('columns', [])):
                    col = line['columns'][total_amt_curr_no_sym_col_idx]
                    col['class'] = 'number total'
                    col['figure_type'] = 'float'
                    col['format_params'] = {'digits': 2}
                    # We remove 'name' to let Odoo's _format_column_values handle the formatting
                    # based on our digits=2 requirement.
                    if 'name' in col:
                        del col['name']
        
        return lines


    def _aged_partner_report_custom_engine_common(self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None):
        report = self.env['account.report'].browse(options['report_id'])
        report._check_groupby_fields((next_groupby.split(',') if next_groupby else []) + ([current_groupby] if current_groupby else []))

        def minus_days(date_obj, days):
            return fields.Date.to_string(date_obj - relativedelta(days=days))

        aging_date_field = SQL.identifier('invoice_date') if options['aging_based_on'] == 'base_on_invoice_date' else SQL.identifier('date_maturity')
        date_to = fields.Date.from_string(options['date']['date_to'])
        interval = options['aging_interval']
        periods = [(False, fields.Date.to_string(date_to))]
        # Since we added the first period in the list we have to do one less iteration
        nb_periods = len([column for column in options['columns'] if column['expression_label'].startswith('period')]) - 1
        for i in range(nb_periods):
            start_date = minus_days(date_to, (interval * i) + 1)
            # The last element of the list will have False for the end date
            end_date = minus_days(date_to, interval * (i + 1)) if i < nb_periods - 1 else False
            periods.append((start_date, end_date))

        def build_result_dict(report, query_res_lines):
            rslt = {f'period{i}': 0 for i in range(len(periods))}
            total_amount_currency = 0

            for query_res in query_res_lines:
                total_amount_currency += query_res['amount_currency']
                for i in range(len(periods)):
                    period_key = f'period{i}'
                    rslt[period_key] += query_res[period_key]

            if current_groupby == 'id':
                query_res = query_res_lines[0] # We're grouping by id, so there is only 1 element in query_res_lines anyway
                currency = self.env['res.currency'].browse(query_res['currency_id'][0]) if len(query_res['currency_id']) == 1 else None

                # Custom Fields Logic
                def get_string_value(val):
                    if isinstance(val, dict):
                        # Handle translated field (jsonb): try user's lang, then en_US, then first value
                        return val.get(self.env.user.lang) or val.get('en_US') or next(iter(val.values()), '')
                    return str(val) if val else ''

                tracking_refs = query_res.get('tracking_refs') or []
                cso_ref_str = ', '.join(sorted(list(set(get_string_value(v) for v in tracking_refs if v)))) if tracking_refs else None
                
                sales_managers = query_res.get('sales_managers') or []
                sales_manager_str = ', '.join(sorted(list(set(get_string_value(v) for v in sales_managers if v)))) if sales_managers else None
                
                due_dates = query_res.get('invoice_due_dates') or []
                min_due_date = min(due_dates) if due_dates else None

                bill_refs = query_res.get('bill_refs') or []
                bill_ref_str = ', '.join(sorted(list(set(get_string_value(v) for v in bill_refs if v)))) if bill_refs else None

                companies = query_res.get('companies') or []
                company_str = ', '.join(sorted(list(set(get_string_value(v) for v in companies if v)))) if companies else None

                rslt.update({
                    'invoice_date': query_res['invoice_date'][0] if len(query_res['invoice_date']) == 1 else None,
                    'due_date': query_res['due_date'][0] if len(query_res['due_date']) == 1 else None,
                    'invoice_date_due': min_due_date,
                    'amount_currency': query_res['amount_currency'],
                    'amount_currency_no_symbol': query_res['amount_currency'],
                    'currency_id': query_res['currency_id'][0] if len(query_res['currency_id']) == 1 else None,
                    'currency': currency.display_name if currency else None,
                    'account_name': query_res['account_name'][0] if len(query_res['account_name']) == 1 else None,
                    'tracking_ref': cso_ref_str,
                    'bill_ref': bill_ref_str,
                    'sales_manager_id': sales_manager_str,
                    'company_id': company_str,
                    'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
                    'has_sublines': True,
                    # Needed by the custom_unfold_all_batch_data_generator, to speed-up unfold_all
                    'partner_id': query_res['partner_id'][0] if query_res['partner_id'] else None,
                })
            else:
                rslt.update({
                    'invoice_date': None,
                    'due_date': None,
                    'invoice_date_due': None,
                    'amount_currency': None,
                    'amount_currency_no_symbol': total_amount_currency,
                    'currency_id': None,
                    'currency': None,
                    'account_name': None,
                    'tracking_ref': None,
                    'bill_ref': None,
                    'sales_manager_id': None,
                    'company_id': None,
                    'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
                    'has_sublines': True,
                })
            
            return rslt

        # Build period table
        period_table_format = ('(VALUES %s)' % ','.join("(%s, %s, %s)" for period in periods))
        params = list(chain.from_iterable(
            (period[0] or None, period[1] or None, i)
            for i, period in enumerate(periods)
        ))
        period_table = SQL(period_table_format, *params)

        # Build query
        query = report._get_report_query(options, 'strict_range', domain=[('account_id.account_type', '=', internal_type)])
        account_alias = query.left_join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
        account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)

        always_present_groupby = SQL("period_table.period_index")
        if current_groupby:
            groupby_field_sql = self.env['account.move.line']._field_to_sql("account_move_line", current_groupby, query)
            select_from_groupby = SQL("%s AS grouping_key,", groupby_field_sql)
            groupby_clause = SQL("%s, %s", groupby_field_sql, always_present_groupby)
        else:
            select_from_groupby = SQL()
            groupby_clause = always_present_groupby
        multiplicator = -1 if internal_type == 'liability_payable' else 1
        select_period_query = SQL(',').join(
            SQL("""
                CASE WHEN period_table.period_index = %(period_index)s
                THEN %(multiplicator)s * SUM(%(balance_select)s)
                ELSE 0 END AS %(column_name)s
                """,
                period_index=i,
                multiplicator=multiplicator,
                column_name=SQL.identifier(f"period{i}"),
                balance_select=report._currency_table_apply_rate(SQL(
                    "account_move_line.balance - COALESCE(part_debit.amount, 0) + COALESCE(part_credit.amount, 0)"
                )),
            )
            for i in range(len(periods))
        )

        tail_query = report._get_engine_query_tail(offset, limit)

        query = SQL(
            """
            WITH period_table(date_start, date_stop, period_index) AS (%(period_table)s)

            SELECT
                %(select_from_groupby)s
                %(multiplicator)s * (
                    SUM(account_move_line.amount_currency)
                    - COALESCE(SUM(part_debit.debit_amount_currency), 0)
                    + COALESCE(SUM(part_credit.credit_amount_currency), 0)
                ) AS amount_currency,
                ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
                ARRAY_AGG(DISTINCT account_move_line.move_id) AS move_id,
                ARRAY_AGG(account_move_line.payment_id) AS payment_id,
                ARRAY_AGG(DISTINCT move.date) AS invoice_date,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date)) AS report_date,
                ARRAY_AGG(DISTINCT %(account_code)s) AS account_name,
                ARRAY_AGG(DISTINCT COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date)) AS due_date,
                ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
                COUNT(account_move_line.id) AS aml_count,
                ARRAY_AGG(%(account_code)s) AS account_code,
                ARRAY_AGG(DISTINCT move.tracking_ref) FILTER (WHERE move.tracking_ref IS NOT NULL) AS tracking_refs,
                ARRAY_AGG(DISTINCT move.ref) FILTER (WHERE move.ref IS NOT NULL) AS bill_refs,
                ARRAY_AGG(DISTINCT move.invoice_date_due) FILTER (WHERE move.invoice_date_due IS NOT NULL) AS invoice_due_dates,
                ARRAY_AGG(DISTINCT hr_employee.name) FILTER (WHERE hr_employee.name IS NOT NULL) AS sales_managers,
                ARRAY_AGG(DISTINCT res_company.name) FILTER (WHERE res_company.name IS NOT NULL) AS companies,
                %(select_period_query)s

            FROM %(table_references)s

            JOIN account_journal journal ON journal.id = account_move_line.journal_id
            LEFT JOIN account_move move ON move.id = account_move_line.move_id
            LEFT JOIN hr_employee ON hr_employee.id = move.sales_manager_id
            LEFT JOIN res_company ON res_company.id = account_move_line.company_id
            %(currency_table_join)s

            LEFT JOIN LATERAL (
                SELECT
                    SUM(part.amount) AS amount,
                    SUM(part.debit_amount_currency) AS debit_amount_currency,
                    part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date_to)s AND part.debit_move_id = account_move_line.id
                GROUP BY part.debit_move_id
            ) part_debit ON TRUE

            LEFT JOIN LATERAL (
                SELECT
                    SUM(part.amount) AS amount,
                    SUM(part.credit_amount_currency) AS credit_amount_currency,
                    part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %(date_to)s AND part.credit_move_id = account_move_line.id
                GROUP BY part.credit_move_id
            ) part_credit ON TRUE

            JOIN period_table ON
                (
                    period_table.date_start IS NULL
                    OR COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date) <= DATE(period_table.date_start)
                )
                AND
                (
                    period_table.date_stop IS NULL
                    OR COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date) >= DATE(period_table.date_stop)
                )

            WHERE %(search_condition)s

            GROUP BY %(groupby_clause)s

            HAVING
                ROUND(SUM(%(having_debit)s), %(currency_precision)s) != 0
                OR ROUND(SUM(%(having_credit)s), %(currency_precision)s) != 0

            ORDER BY %(groupby_clause)s

            %(tail_query)s
            """,
            account_code=account_code,
            period_table=period_table,
            select_from_groupby=select_from_groupby,
            select_period_query=select_period_query,
            multiplicator=multiplicator,
            aging_date_field=aging_date_field,
            table_references=query.from_clause,
            currency_table_join=report._currency_table_aml_join(options),
            date_to=date_to,
            search_condition=query.where_clause,
            groupby_clause=groupby_clause,
            having_debit=report._currency_table_apply_rate(SQL("CASE WHEN account_move_line.balance > 0  THEN account_move_line.balance else 0 END - COALESCE(part_debit.amount, 0)")),
            having_credit=report._currency_table_apply_rate(SQL("CASE WHEN account_move_line.balance < 0  THEN -account_move_line.balance else 0 END - COALESCE(part_credit.amount, 0)")),
            currency_precision=self.env.company.currency_id.decimal_places,
            tail_query=tail_query,
        )

        self.env.cr.execute(query)
        query_res_lines = self.env.cr.dictfetchall()

        if not current_groupby:
            return build_result_dict(report, query_res_lines)
        else:
            rslt = []

            all_res_per_grouping_key = {}
            for query_res in query_res_lines:
                grouping_key = query_res['grouping_key']
                all_res_per_grouping_key.setdefault(grouping_key, []).append(query_res)

            for grouping_key, query_res_lines in all_res_per_grouping_key.items():
                rslt.append((grouping_key, build_result_dict(report, query_res_lines)))

            return rslt

    def _prepare_partner_values(self):
        return {
            'invoice_date': None,
            'due_date': None,
            'invoice_date_due': None,
            'amount_currency': None,
            'currency_id': None,
            'currency': None,
            'account_name': None,
            'tracking_ref': None,
            'bill_ref': None,
            'sales_manager_id': None,
            'company_id': None,
            'total': 0,
        }
