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

    def _get_inter_company_account_type_for_report(self):
        self.ensure_one()
        for account_type_id, config in INTER_COMPANY_ACCOUNT_TYPE_CONFIG.items():
            if self.custom_handler_model_name == config['handler']:
                return account_type_id
        return None

    def _init_options_account_type(self, options, previous_options):
        super()._init_options_account_type(options, previous_options)
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
    def _get_options_account_type_domain(self, options):
        if not options.get('account_type'):
            return super()._get_options_account_type_domain(options)

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
