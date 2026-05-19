# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime

class AcademicYear(models.Model):
    """To manage with Academic year"""
    _name = 'academic.year'
    _description = 'Academic Year'
    _rec_name = 'name'
    _order = 'start_year desc'

    name = fields.Char(string='Name', compute='_compute_academic_year_name', store=True)
    start_year = fields.Selection(
        selection='get_year_selection',
        string='Start Year',
        required=True)
    end_year = fields.Selection(
        selection='get_year_selection',
        string='End Year',
        required=True)

    _name_uniq = models.Constraint(
        'unique (name)',
        'Academic Year name must be unique!',
    )

    @api.constrains('name')
    def _check_name_unique(self):
        for record in self:
            if self.search_count([('name', '=', record.name), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Academic Year name must be unique!"))

    @api.constrains('start_year', 'end_year')
    def _check_years(self):
        for record in self:
            if record.start_year and record.end_year:
                if int(record.end_year) != int(record.start_year) + 1:
                    raise ValidationError(_("End Year must be exactly one year after Start Year (e.g., 2023-2024)."))

    @api.model
    def get_year_selection(self):
        """Fetch years for selection from 10 years ago to next year"""
        current_year = datetime.now().year
        return [(str(year), str(year)) for year in range(current_year - 10, current_year + 2)]

    @api.depends('start_year', 'end_year')
    def _compute_academic_year_name(self):
        for period in self:
            if period.start_year and period.end_year:
                period.name = f"{period.start_year} - {period.end_year}"
            else:
                period.name = False
