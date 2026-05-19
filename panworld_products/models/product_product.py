# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_not_compare = fields.Boolean(
        string='Is not compare',
        required=False
    )
    uk_wholesaler_id = fields.Many2one(
        comodel_name="res.partner",
        string="UK Wholesalers",
        domain=lambda self: "[('category_id', 'in', %s)]"
        % [self.env.ref("panworld_contact.res_partner_category_uk_wholesaler").id],
    )
    non_uk_wholesaler_id = fields.Many2one(
        comodel_name="res.partner",
        string="Non-UK Wholesalers",
        domain=lambda self: "[('category_id', 'in', %s)]"
        % [self.env.ref("panworld_contact.res_partner_category_non_ukwholesaler").id],
    )
    main_title = fields.Char(string="Main Title")
    subtitle = fields.Char(string="Subtitle", readonly=False)
    subject = fields.Char(string="Subject")
    page = fields.Integer(string="Page")
    edition = fields.Integer(string="Edition")
    series = fields.Float(string="Series")
    book_language_id = fields.Many2one(
        comodel_name="res.lang", string="Book Language")
    interest_age = fields.Float(string="Interest Age")
    audience_readership = fields.Selection([('single', 'Single'), ('bundle_of_2', 'Bundle of 2+1'), ('bundle_of_3', 'Bundle of 3+1'), ('bundle_of_4', 'Bundle of 4+1')], string="Single/ Bundle")
    publication_date = fields.Date(string="ASIN")
    status = fields.Selection(
        [("available", "Available"), ("upcoming", "Upcoming")],
        string="Status",
        default="available",
    )
    cubiscan_device = fields.Integer(string="Cubiscan device")
    sub_category_id = fields.Many2one("product.sub.category",
                                      string="Product Sub Category",
                                      ondelete="restrict", index=True)

    @api.onchange("name")
    def _onchange_main_title(self):
        """this method allows to set main title taken into name field"""
        self.main_title = self.name

    @api.onchange("main_title")
    def _onchange_subtitle(self):
        """this method allows to set subtitle taken into name main title"""
        self.subtitle = self.main_title

    @api.onchange("barcode")
    def _onchange_barcode(self):
        """ when we add barcode then set as internal reference to display on product."""
        self.default_code = self.barcode
