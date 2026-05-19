# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.fields import Domain

INTER_COMPANY_RECEIVABLE_ACCOUNT_TYPE = 'inter_company_receivable'
INTER_COMPANY_PAYABLE_ACCOUNT_TYPE = 'inter_company_payable'

INTER_COMPANY_ACCOUNT_TYPE_CONFIG = {
    INTER_COMPANY_RECEIVABLE_ACCOUNT_TYPE: {
        'handler': 'account.aged.receivable.report.handler',
        'label': lambda self: _('Inter Company Receivable'),
        'account_type': 'asset_receivable',
        'move_types': ('out_invoice', 'out_refund'),
    },
    INTER_COMPANY_PAYABLE_ACCOUNT_TYPE: {
        'handler': 'account.aged.payable.report.handler',
        'label': lambda self: _('Inter Company Payable'),
        'account_type': 'liability_payable',
        'move_types': ('in_invoice', 'in_refund'),
    },
}


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def _is_aged_receivable_report(self):
        self.ensure_one()
        return (
            self.filter_account_type == 'receivable'
            and self.custom_handler_model_name == 'account.aged.receivable.report.handler'
        )

    def _is_aged_payable_report(self):
        self.ensure_one()
        return (
            self.filter_account_type == 'payable'
            and self.custom_handler_model_name == 'account.aged.payable.report.handler'
        )

    def _get_inter_company_account_type_for_report(self):
        self.ensure_one()
        for account_type_id, config in INTER_COMPANY_ACCOUNT_TYPE_CONFIG.items():
            if self.custom_handler_model_name == config['handler']:
                return account_type_id
        return None

    def _init_options_account_type(self, options, previous_options):
        super()._init_options_account_type(options, previous_options)
        if self._is_aged_receivable_report():
            for account_type in options.get('account_type', []):
                if account_type['id'] == 'trade_receivable':
                    account_type['name'] = _('Customer Receivable')
        if self._is_aged_payable_report():
            for account_type in options.get('account_type', []):
                if account_type['id'] == 'trade_payable':
                    account_type['name'] = _('Publisher Payable')

        inter_company_account_type_id = self._get_inter_company_account_type_for_report()
        if not inter_company_account_type_id:
            return

        config = INTER_COMPANY_ACCOUNT_TYPE_CONFIG[inter_company_account_type_id]
        inter_company_opt = {
            'id': inter_company_account_type_id,
            'name': config['label'](self),
            'selected': False,
        }
        options['account_type'].append(inter_company_opt)

        if previous_options.get('account_type'):
            previously_selected_ids = {
                account_type['id']
                for account_type in previous_options['account_type']
                if account_type.get('selected')
            }
            inter_company_opt['selected'] = inter_company_account_type_id in previously_selected_ids

    @api.model
    def _get_inter_company_partner_ids(self):
        return self.env['res.company'].search([]).partner_id.ids

    @api.model
    def _get_inter_company_account_type_domain(self, account_type_id):
        config = INTER_COMPANY_ACCOUNT_TYPE_CONFIG[account_type_id]
        company_partner_ids = self._get_inter_company_partner_ids()
        return Domain([
            ('account_id.account_type', '=', config['account_type']),
            ('partner_id', 'in', company_partner_ids or [0]),
            ('move_id.move_type', 'in', config['move_types']),
        ])

    @api.model
    def _get_customer_receivable_domain(self):
        """Trade receivables on customer invoices only, excluding inter-company (company) partners."""
        company_partner_ids = self._get_inter_company_partner_ids()
        exclude_partners = company_partner_ids or [0]
        return Domain([
            ('account_id.non_trade', '=', False),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('move_id.move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'not in', exclude_partners),
        ])

    @api.model
    def _get_publisher_payable_domain(self):
        """Trade payables on vendor bills only, excluding inter-company (company) partners."""
        company_partner_ids = self._get_inter_company_partner_ids()
        exclude_partners = company_partner_ids or [0]
        return Domain([
            ('account_id.non_trade', '=', False),
            ('account_id.account_type', '=', 'liability_payable'),
            ('move_id.move_type', 'in', ('in_invoice', 'in_refund')),
            ('partner_id', 'not in', exclude_partners),
        ])

    @api.model
    def _get_aged_receivable_account_type_domain(self, options):
        domain_by_id = {
            'trade_receivable': self._get_customer_receivable_domain(),
            'non_trade_receivable': Domain([
                ('account_id.non_trade', '=', True),
                ('account_id.account_type', '=', 'asset_receivable'),
            ]),
            INTER_COMPANY_RECEIVABLE_ACCOUNT_TYPE: self._get_inter_company_account_type_domain(
                INTER_COMPANY_RECEIVABLE_ACCOUNT_TYPE,
            ),
        }
        selected_domains = []
        all_domains = []
        for account_type in options.get('account_type', []):
            domain = domain_by_id.get(account_type['id'])
            if domain is None:
                continue
            if account_type['selected']:
                selected_domains.append(domain)
            all_domains.append(domain)
        if not all_domains:
            return super()._get_options_account_type_domain(options)
        return Domain.OR(selected_domains or all_domains)

    @api.model
    def _get_aged_payable_account_type_domain(self, options):
        domain_by_id = {
            'trade_payable': self._get_publisher_payable_domain(),
            'non_trade_payable': Domain([
                ('account_id.non_trade', '=', True),
                ('account_id.account_type', '=', 'liability_payable'),
            ]),
            INTER_COMPANY_PAYABLE_ACCOUNT_TYPE: self._get_inter_company_account_type_domain(
                INTER_COMPANY_PAYABLE_ACCOUNT_TYPE,
            ),
        }
        selected_domains = []
        all_domains = []
        for account_type in options.get('account_type', []):
            domain = domain_by_id.get(account_type['id'])
            if domain is None:
                continue
            if account_type['selected']:
                selected_domains.append(domain)
            all_domains.append(domain)
        if not all_domains:
            return super()._get_options_account_type_domain(options)
        return Domain.OR(selected_domains or all_domains)

    @api.model
    def _get_options_account_type_domain(self, options):
        if not options.get('account_type'):
            return super()._get_options_account_type_domain(options)

        report = (
            self.env['account.report'].browse(options['report_id'])
            if options.get('report_id')
            else self.env['account.report']
        )
        if report and report.filter_account_type == 'receivable' and report.custom_handler_model_name == 'account.aged.receivable.report.handler':
            return self._get_aged_receivable_account_type_domain(options)
        if report and report.filter_account_type == 'payable' and report.custom_handler_model_name == 'account.aged.payable.report.handler':
            return self._get_aged_payable_account_type_domain(options)

        selected_inter_company_types = [
            account_type['id']
            for account_type in options['account_type']
            if account_type.get('selected') and account_type['id'] in INTER_COMPANY_ACCOUNT_TYPE_CONFIG
        ]
        if not selected_inter_company_types:
            return super()._get_options_account_type_domain(options)

        standard_account_types = [
            account_type for account_type in options['account_type']
            if account_type['id'] not in INTER_COMPANY_ACCOUNT_TYPE_CONFIG
        ]
        if any(account_type.get('selected') for account_type in standard_account_types):
            standard_domain = super()._get_options_account_type_domain({
                **options,
                'account_type': standard_account_types,
            })
        else:
            standard_domain = Domain.FALSE

        inter_company_domain = Domain.FALSE
        for account_type_id in selected_inter_company_types:
            inter_company_domain |= self._get_inter_company_account_type_domain(account_type_id)
        return standard_domain | inter_company_domain

    def _caret_options_initializer_default(self):
        res = super()._caret_options_initializer_default()
        if 'account.account' in res:
            res['account.account'].append({'name': _("Journal Items"), 'action': 'caret_option_open_journal_items'})
        return res

    def caret_option_open_journal_items(self, options, params):
        model, record_id = self._get_model_info_from_id(params['line_id'])
        if model != 'account.account':
            return
            
        account = self.env['account.account'].browse(record_id)
        
        # Get date domain from options
        date_from = options['date'].get('date_from')
        date_to = options['date'].get('date_to')
        
        domain = [('account_id', '=', account.id)]
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
            
        # Add journal filter if applicable
        journal_domain = self._get_options_journals_domain(options)
        if journal_domain:
            domain += journal_domain
            
        # Add company filter
        company_ids = self.get_report_company_ids(options)
        if company_ids:
            domain.append(('company_id', 'in', company_ids))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Items (%s)') % account.display_name,
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'domain': domain,
            'context': {**self.env.context, 'search_default_posted': 1},
        }
