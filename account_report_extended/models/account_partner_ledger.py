# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import formatLang
from odoo.tools import SQL
from collections import defaultdict

class AccountPartnerLedgerReportHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _get_additional_column_aml_values(self):
        return SQL("account_move.ref AS bill_ref,")

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=0):
        # Ensure our custom columns have values
        if 'amount_currency_no_symbol' not in aml_query_result:
            aml_query_result['amount_currency_no_symbol'] = aml_query_result.get('amount_currency', 0.0)
        
        if 'bill_ref' not in aml_query_result:
            aml_query_result['bill_ref'] = ''

        # Call super to get the basic line structure
        res = super()._get_report_line_move_line(options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=level_shift)
        
        # Populate values if they are empty (for company currency)
        report = self.env['account.report'].browse(options['report_id'])
        currency_id = aml_query_result.get('currency_id')
        currency = self.env['res.currency'].browse(currency_id) if currency_id else self.env.company.currency_id
        val = aml_query_result.get('amount_currency', 0.0)
        
        for i, col in enumerate(options['columns']):
            expr = col.get('expression_label')
            if expr == 'amount_currency':
                # Force visibility of the value with symbol even for company currency
                res['columns'][i] = report._build_column_dict(val, col, options=options, currency=currency)
            elif expr == 'amount_currency_no_symbol':
                res['columns'][i] = report._build_column_dict(val, col, options=options)
            elif expr == 'bill_ref':
                bill_ref = aml_query_result.get('bill_ref') or ''
                res['columns'][i] = report._build_column_dict(bill_ref, col, options=options)

        return res

    def _custom_line_postprocessor(self, report, options, lines):
        # Apply standard post-processing
        lines = super()._custom_line_postprocessor(report, options, lines)
        
        cols = options.get('columns', [])
        col_idx = next((i for i, c in enumerate(cols) if c.get('expression_label') == 'amount_currency_no_symbol'), None)
        amt_curr_col_idx = next((i for i, c in enumerate(cols) if c.get('expression_label') == 'amount_currency'), None)
        
        if col_idx is None and amt_curr_col_idx is None:
            return lines

        # Populate partner lines with total currency amount if they have a single currency
        partner_indices = {}
        total_line_idx = None
        for i, line in enumerate(lines):
            markup = report._parse_line_id(line['id'])[-1][0]
            if markup == 'total':
                total_line_idx = i
                continue
                
            model, model_id = report._get_model_info_from_id(line['id'])
            if model == 'res.partner' and model_id:
                partner_indices[model_id] = i
        
        # Fetch data for partners and for the total report line
        account_types = ['asset_receivable', 'liability_payable']
        if options.get('filter_account_type') == 'receivable':
            account_types = ['asset_receivable']
        elif options.get('filter_account_type') == 'payable':
            account_types = ['liability_payable']

        state_domain = [('parent_state', '=', 'posted')]
        if options.get('filter_show_draft'):
            state_domain = [('parent_state', 'in', ('posted', 'draft'))]

        domain = [
            ('account_id.account_type', 'in', account_types),
            ('date', '<=', options['date']['date_to']),
        ] + state_domain
        
        # Filter by company
        company_ids = report.get_report_company_ids(options)
        domain.append(('company_id', 'in', company_ids))

        # Query AMLs for currency totals
        # We need this for the total report line anyway
        aml_groups = self.env['account.move.line'].read_group(
            domain,
            ['partner_id', 'currency_id', 'amount_currency'],
            ['partner_id', 'currency_id'],
            lazy=False
        )
        
        partner_currency_map = {} # pid -> {curr_id: total}
        overall_currency_map = {} # curr_id -> total
        
        for group in aml_groups:
            pid = group['partner_id'][0] if group['partner_id'] else None
            cid = group['currency_id'][0] if group['currency_id'] else None
            amt = group['amount_currency']
            
            overall_currency_map[cid] = overall_currency_map.get(cid, 0.0) + amt
            if pid:
                if pid not in partner_currency_map:
                    partner_currency_map[pid] = {}
                partner_currency_map[pid][cid] = partner_currency_map[pid].get(cid, 0.0) + amt
        
        # Update Partner Lines
        for pid, idx in partner_indices.items():
            currencies = partner_currency_map.get(pid, {})
            if len(currencies) == 1:
                currency_id, total_amt = list(currencies.items())[0]
                currency = self.env['res.currency'].browse(currency_id)
                line_cols = lines[idx].get('columns', [])
                
                if col_idx is not None and col_idx < len(line_cols):
                    line_cols[col_idx]['no_format'] = total_amt
                
                if amt_curr_col_idx is not None and amt_curr_col_idx < len(line_cols):
                    line_cols[amt_curr_col_idx]['no_format'] = total_amt
                    line_cols[amt_curr_col_idx]['name'] = formatLang(self.env, total_amt, currency_obj=currency)

        # Update Total Report Line
        if total_line_idx is not None:
            # We always show the sum in our custom column (no symbol)
            total_amt_currency = sum(overall_currency_map.values())
            line_cols = lines[total_line_idx].get('columns', [])
            if col_idx is not None and col_idx < len(line_cols):
                line_cols[col_idx]['no_format'] = total_amt_currency
            
            # For the one with symbol, only show if single currency
            if amt_curr_col_idx is not None and amt_curr_col_idx < len(line_cols):
                if len(overall_currency_map) == 1:
                    cid, total_amt = list(overall_currency_map.items())[0]
                    currency = self.env['res.currency'].browse(cid)
                    line_cols[amt_curr_col_idx]['no_format'] = total_amt
                    line_cols[amt_curr_col_idx]['name'] = formatLang(self.env, total_amt, currency_obj=currency)
                else:
                    line_cols[amt_curr_col_idx]['name'] = ''
                    line_cols[amt_curr_col_idx]['no_format'] = 0.0

        # Force right alignment and digits for the custom column on ALL lines
        if col_idx is not None:
            for line in lines:
                if col_idx < len(line.get('columns', [])):
                    col = line['columns'][col_idx]
                    col['class'] = 'number'
                    col['figure_type'] = 'float'
                    col['format_params'] = {'digits': 2}
                    if 'name' in col:
                        del col['name']
        
        return lines

    def _get_initial_balance_values(self, partner_ids, options):
        queries = []
        report = self.env.ref('account_reports.partner_ledger_report')
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            new_options = self._get_options_initial_balance(column_group_options)
            query = report._get_report_query(new_options, 'from_beginning', domain=[('partner_id', 'in', partner_ids)])
            queries.append(SQL(
                """
                SELECT
                    account_move_line.partner_id                            AS groupby,
                    %(column_group_key)s                                    AS column_group_key,
                    0                                                       AS debit,
                    0                                                       AS credit,
                    SUM(%(balance_select)s)                                 AS amount,
                    SUM(%(balance_select)s)                                 AS balance,
                    SUM(account_move_line.amount_currency)                 AS amount_currency,
                    ARRAY_AGG(DISTINCT account_move_line.currency_id)      AS currency_ids
                FROM %(table_references)s
                %(currency_table_join)s
                WHERE %(search_condition)s
                GROUP BY account_move_line.partner_id
                """,
                column_group_key=column_group_key,
                balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(column_group_options),
                search_condition=query.where_clause,
            ))

        self.env.cr.execute(SQL(" UNION ALL ").join(queries))

        init_balance_by_col_group = {
            partner_id: {column_group_key: defaultdict(float) for column_group_key in options['column_groups']}
            for partner_id in partner_ids
        }
        for result in self.env.cr.dictfetchall():
            pid = result['groupby']
            cgk = result['column_group_key']
            init_balance_by_col_group[pid][cgk] = result
            # Inject our custom field
            result['amount_currency_no_symbol'] = result['amount_currency']

        # Correct the sums per partner
        new_options = self._get_options_initial_balance(options)
        self._add_sums_of_lines_without_partners(new_options, init_balance_by_col_group)

        return init_balance_by_col_group

    def _get_sums_without_partner(self, options):
        queries = []
        report = self.env.ref('account_reports.partner_ledger_report')
        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            partner_ids = column_group_options.pop('partner_ids', [])
            query = report._get_report_query(column_group_options, 'from_beginning')
            queries.append(SQL(
                """
                SELECT
                    %(column_group_key)s        AS column_group_key,
                    aml_with_partner.partner_id AS groupby,
                    SUM(%(debit_select)s)       AS debit,
                    SUM(%(credit_select)s)      AS credit,
                    SUM(%(balance_select)s)     AS amount,
                    SUM(%(balance_select)s)     AS balance,
                    SUM(CASE WHEN account_move_line.balance != 0 THEN (partial.amount / ABS(account_move_line.balance)) * account_move_line.amount_currency ELSE 0 END) AS amount_currency
                FROM %(table_references)s
                JOIN account_partial_reconcile partial
                    ON account_move_line.id = partial.debit_move_id OR account_move_line.id = partial.credit_move_id
                JOIN account_move_line aml_with_partner ON
                    (aml_with_partner.id = partial.debit_move_id OR aml_with_partner.id = partial.credit_move_id)
                    AND aml_with_partner.partner_id IS NOT NULL
                %(currency_table_join)s
                WHERE partial.max_date <= %(date_to)s AND %(search_condition)s
                    AND account_move_line.partner_id IS NULL
                    %(partner_id_constraint)s
                GROUP BY aml_with_partner.partner_id
                """,
                column_group_key=column_group_key,
                debit_select=report._currency_table_apply_rate(SQL("CASE WHEN aml_with_partner.balance > 0 THEN 0 ELSE partial.amount END")),
                credit_select=report._currency_table_apply_rate(SQL("CASE WHEN aml_with_partner.balance < 0 THEN 0 ELSE partial.amount END")),
                balance_select=report._currency_table_apply_rate(SQL("-SIGN(aml_with_partner.balance) * partial.amount")),
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(column_group_options, aml_alias=SQL("aml_with_partner")),
                date_to=column_group_options['date']['date_to'],
                search_condition=query.where_clause,
                partner_id_constraint=SQL(' AND aml_with_partner.partner_id IN %s', tuple(partner_ids)) if partner_ids else SQL(''),
            ))

        return SQL(" UNION ALL ").join(queries)

    def _report_expand_unfoldable_line_partner_ledger(self, line_dict_id, groupby, options, progress, offset, unfold_all_batch_data=None):
        report = self.env['account.report'].browse(options['report_id'])
        markup, model, record_id = report._parse_line_id(line_dict_id)[-1]
        
        # Standard expansion
        res = super()._report_expand_unfoldable_line_partner_ledger(line_dict_id, groupby, options, progress, offset, unfold_all_batch_data=unfold_all_batch_data)
        
        # Fixing Initial Balance line if added
        if offset == 0 and res.get('lines') and any(l.get('name') == _("Initial Balance") for l in res['lines']):
            init_line = next(l for l in res['lines'] if l.get('name') == _("Initial Balance"))
            
            if unfold_all_batch_data:
                 init_vals_by_cgk = unfold_all_batch_data['initial_balances'].get(record_id, {})
            else:
                 init_vals_by_cgk = self._get_initial_balance_values([record_id], options).get(record_id, {})
            
            for cgk, vals in init_vals_by_cgk.items():
                currency_ids = vals.get('currency_ids', [])
                currency = self.env['res.currency'].browse(currency_ids[0]) if currency_ids and len(currency_ids) == 1 else None
                
                for i, col_opt in enumerate(options['columns']):
                    if col_opt.get('column_group_key') == cgk:
                        expr = col_opt.get('expression_label')
                        if expr in ('amount_currency', 'amount_currency_no_symbol'):
                            val = vals.get('amount_currency', 0.0)
                            if i < len(init_line['columns']):
                                if expr == 'amount_currency':
                                     init_line['columns'][i] = report._build_column_dict(val, col_opt, options=options, currency=currency)
                                else:
                                     init_line['columns'][i] = report._build_column_dict(val, col_opt, options=options)
        return res
