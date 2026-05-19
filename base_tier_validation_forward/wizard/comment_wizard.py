# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models


class CommentWizard(models.TransientModel):
    _inherit = "comment.wizard"

    def add_comment(self):
        super().add_comment()
        rec = self.env[self.res_model].browse(self.res_id)
        if self.validate_reject == "forward":
            rec._forward_tier(self.review_ids)
        rec._update_counter({"review_created": True})
        return self.review_ids
