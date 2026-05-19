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


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_storable = fields.Boolean(default=True)
    uk_wholesaler_id = fields.Many2one(
        comodel_name="product.grade",
        string="Grade",
    )
    non_uk_wholesaler_id = fields.Many2one(
        comodel_name="product.classification",
        string="Classification",
    )

    main_title = fields.Char(
        compute="_compute_main_title", inverse="_set_main_title", string="Main Title"
    )
    subtitle = fields.Many2one(
        comodel_name="product.subtitle",
        string="Format",
        readonly=False,
    )
    subject = fields.Many2one(string="Subject", comodel_name="product.subject",
                              )
    page = fields.Integer(compute="_compute_page", inverse="_set_page", string="Page")
    edition = fields.Integer(
        compute="_compute_edition", inverse="_set_edition", string="Edition"
    )
    series = fields.Float(
        compute="_compute_series", inverse="_set_series", string="Series"
    )
    book_language_id = fields.Many2one(
        compute="_compute_book_language_id",
        inverse="_set_book_language_id",
        comodel_name="res.lang",
        string="Book Language",
    )
    interest_age = fields.Float(
        compute="_compute_interest_age",
        inverse="_set_interest_age",
        string="Interest Age",
    )
    audience_readership = fields.Selection([('single', 'Single'), ('bundle_of_2', 'Bundle of 2+1'), ('bundle_of_3', 'Bundle of 3+1'), ('bundle_of_4', 'Bundle of 4+1')],
        compute="_compute_audience_readership",
        inverse="_set_audience_readership",
        string="Single/ Bundle",
    )
    publication_date = fields.Date(
        compute="_compute_publication_date",
        inverse="_set_publication_date",
        string="ASIN",
    )
    status = fields.Selection(
        compute="_compute_status",
        inverse="_set_status",
        selection=[("available", "Available"), ("upcoming", "Upcoming")],
        string="Status",
        default="available",
    )
    cubiscan_device = fields.Integer(
        compute="_compute_cubiscan_device",
        inverse="_set_cubiscan_device",
        string="Cubiscan device",
    )

    # Common Fields
    author_id = fields.Many2one(
        comodel_name="res.partner",
        string="Author",
        domain=lambda self: "[('category_id', 'in', %s)]"
                            % [self.env.ref("panworld_contact.res_partner_category_author").id],
    )
    publisher_id = fields.Many2one(
        comodel_name="res.partner",
        required=True,
        string="Publisher",
        domain=lambda self: "[('category_id', 'in', %s)]"
                            % [self.env.ref("panworld_contact.res_partner_category_publisher").id],
    )
    master_publisher_id = fields.Many2one(
        comodel_name="res.partner",
        string="Master Publisher",
        domain=lambda self: "[('category_id', 'in', %s)]"
                            % [self.env.ref("panworld_contact.res_partner_category_master").id],
    )
    publication_country_id = fields.Many2one(
        comodel_name="res.country", string="Publication Country"
    )
    product_format = fields.Selection(
        [("book", "Book"), ("cards", "Cards"), ("audio", "Audio"), ("hw","Hardware")],
        string="Product Format",
        default="book",
    )
    sub_category_id = fields.Many2one("product.sub.category",
                                      string="Product Sub Category",
                                      ondelete="restrict", index=True)

    @api.model_create_multi
    def create(self, vals_list):
        """ Store the initial standard price in order to be able to retrieve the cost of a product template for a given date"""
        templates = super(ProductTemplate, self).create(vals_list)
        # This is needed to set given values to first variant after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            if vals.get("uk_wholesaler_id"):
                related_vals["uk_wholesaler_id"] = vals["uk_wholesaler_id"]
            if vals.get("non_uk_wholesaler_id"):
                related_vals["non_uk_wholesaler_id"] = vals["non_uk_wholesaler_id"]
            if vals.get("main_title"):
                related_vals["main_title"] = vals["main_title"]
            if vals.get("subtitle"):
                related_vals["subtitle"] = vals["subtitle"]
            if vals.get("subject"):
                related_vals["subject"] = vals["subject"]
            if vals.get("page"):
                related_vals["page"] = vals["page"]
            if vals.get("edition"):
                related_vals["edition"] = vals["edition"]
            if vals.get("series"):
                related_vals["series"] = vals["series"]
            if vals.get("book_language_id"):
                related_vals["book_language_id"] = vals["book_language_id"]
            if vals.get("interest_age"):
                related_vals["interest_age"] = vals["interest_age"]
            if vals.get("audience_readership"):
                related_vals["audience_readership"] = vals["audience_readership"]
            if vals.get("publication_date"):
                related_vals["publication_date"] = vals["publication_date"]
            if vals.get("status"):
                related_vals["status"] = vals["status"]
            if vals.get("cubiscan_device"):
                related_vals["cubiscan_device"] = vals["cubiscan_device"]
            if related_vals:
                template.write(related_vals)
        return templates

    # Field which vary variant by variant
    @api.depends("product_variant_ids.uk_wholesaler_id")
    def _compute_uk_wholesaler_id(self):
        self.uk_wholesaler_id = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.uk_wholesaler_id = (
                    template.product_variant_ids.uk_wholesaler_id.id
                )
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.uk_wholesaler_id = archived_variants.uk_wholesaler_id.id

    def _set_uk_wholesaler_id(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.uk_wholesaler_id = self.uk_wholesaler_id.id

    @api.depends("product_variant_ids.non_uk_wholesaler_id")
    def _compute_non_uk_wholesaler_id(self):
        self.non_uk_wholesaler_id = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.non_uk_wholesaler_id = (
                    template.product_variant_ids.non_uk_wholesaler_id.id
                )
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.non_uk_wholesaler_id = (
                        archived_variants.non_uk_wholesaler_id.id
                    )

    def _set_non_uk_wholesaler_id(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.non_uk_wholesaler_id = self.non_uk_wholesaler_id.id

    @api.depends("product_variant_ids.main_title")
    def _compute_main_title(self):
        self.main_title = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.main_title = template.product_variant_ids.main_title
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.main_title = archived_variants.main_title

    def _set_main_title(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.main_title = self.main_title

    @api.depends("product_variant_ids.subtitle")
    def _compute_subtitle(self):
        self.subtitle = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.subtitle = template.product_variant_ids.subtitle
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.subtitle = archived_variants.subtitle

    def _set_subtitle(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.subtitle = self.subtitle

    @api.depends("product_variant_ids.subject")
    def _compute_subject(self):
        self.subject = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.subject = template.product_variant_ids.subject
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.subject = archived_variants.subject

    def _set_subject(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.subject = self.subject

    @api.depends("product_variant_ids.page")
    def _compute_page(self):
        self.page = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.page = template.product_variant_ids.page
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.page = archived_variants.page

    def _set_page(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.page = self.page

    @api.depends("product_variant_ids.edition")
    def _compute_edition(self):
        self.edition = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.edition = template.product_variant_ids.edition
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.edition = archived_variants.edition

    def _set_edition(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.edition = self.edition

    @api.depends("product_variant_ids.series")
    def _compute_series(self):
        self.series = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.series = template.product_variant_ids.series
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.series = archived_variants.series

    def _set_series(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.series = self.series

    @api.depends("product_variant_ids.book_language_id")
    def _compute_book_language_id(self):
        self.book_language_id = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.book_language_id = (
                    template.product_variant_ids.book_language_id.id
                )
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.book_language_id = archived_variants.book_language_id.id

    def _set_book_language_id(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.book_language_id = self.book_language_id.id

    @api.depends("product_variant_ids.interest_age")
    def _compute_interest_age(self):
        self.interest_age = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.interest_age = template.product_variant_ids.interest_age
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.interest_age = archived_variants.interest_age

    def _set_interest_age(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.interest_age = self.interest_age

    @api.depends("product_variant_ids.audience_readership")
    def _compute_audience_readership(self):
        self.audience_readership = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.audience_readership = (
                    template.product_variant_ids.audience_readership
                )
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.audience_readership = archived_variants.audience_readership

    def _set_audience_readership(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.audience_readership = self.audience_readership

    @api.depends("product_variant_ids.publication_date")
    def _compute_publication_date(self):
        self.publication_date = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.publication_date = (
                    template.product_variant_ids.publication_date
                )
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.publication_date = archived_variants.publication_date

    def _set_publication_date(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.publication_date = self.publication_date

    @api.depends("product_variant_ids.status")
    def _compute_status(self):
        self.status = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.status = template.product_variant_ids.status
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.status = archived_variants.status

    def _set_status(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.status = self.status

    @api.depends("product_variant_ids.cubiscan_device")
    def _compute_cubiscan_device(self):
        self.cubiscan_device = False
        for template in self:
            # TODO master: update product_variant_count depends and use it instead
            variant_count = len(template.product_variant_ids)
            if variant_count == 1:
                template.cubiscan_device = template.product_variant_ids.cubiscan_device
            elif variant_count == 0:
                archived_variants = template.with_context(
                    active_test=False
                ).product_variant_ids
                if len(archived_variants) == 1:
                    template.cubiscan_device = archived_variants.cubiscan_device

    def _set_cubiscan_device(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.cubiscan_device = self.cubiscan_device


    @api.onchange("barcode")
    def _onchange_barcode(self):
        """ when we add barcode then set as internal reference to display on product."""
        self.default_code = self.barcode
