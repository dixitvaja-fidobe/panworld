# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models


class TierDefinition(models.Model):
    _inherit = "tier.definition"

    has_forward = fields.Boolean(
        string="Allow Forward",
        default=False,
        help="Allow option to 'Forward' to different person.",
    )
