# -*- coding: utf-8 -*-

from odoo import models, fields, _, api

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

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
