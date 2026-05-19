# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models, fields


class ConfSettings(models.TransientModel):
    """inheriting configuration settings."""
    _inherit = "res.config.settings"

    user_password_restrict = fields.Boolean(string="Restrict User Password",
                                            help="Tick this to enable password"
                                                 "restriction", default=True)
    is_strength = fields.Boolean(string="Should have 8 characters",
                                 help="Enable this to check for 8 characters",
                                 config_parameter='user_password_strength.'
                                                  'is_strength')
    is_digit = fields.Boolean(string="Should have at least one number",
                              help="Enable this to check for at least a digit",
                              config_parameter='user_password_strength.'
                                               'is_digit')
    is_upper = fields.Boolean(string="Should have at least one uppercase",
                              help="Enable this to check for uppercase letter",
                              config_parameter='user_password_strength.'
                                               'is_upper')
    is_lower = fields.Boolean(string="Should have at least one "
                                     "lowercase character",
                              help="Enable this to check for lowercase letter",
                              config_parameter='user_password_strength.'
                                               'is_lower')
    is_special_symbol = fields.Boolean(string="Should have at least one "
                                              "special symbol",
                                       help="Enable this to check for "
                                            "special symbol",
                                       config_parameter='user_password_strength'
                                                        '.is_special_symbol')
