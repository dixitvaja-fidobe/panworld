# -*- coding: utf-8 -*-

from odoo import models, api, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def _format_aml_name(self, line_name, move_ref, move_name=None):
        """ Format the display of an account.move.line record.
        Overridden to only show the sequence (move name) and skip the reference/description
        as requested by the user for cleaner reports.
        """
        if move_name and move_name != '/':
            return move_name
        return line_name or _('Draft Entry')
