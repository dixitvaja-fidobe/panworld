
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import timedelta
from itertools import groupby
from odoo.tools import groupby as groupbyelem
from operator import itemgetter

from odoo import _, api, fields, models, Command
from odoo.tools.misc import clean_context, OrderedSet
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class MailingContact(models.Model):
    _inherit = "mailing.contact"


    name = fields.Char(tracking=True)
    email = fields.Char('Email',tracking=True)
    country_id = fields.Many2one('res.country', string='Country',tracking=True)
    source_name = fields.Char(string='Source')
    title_name = fields.Char(string='Title')
    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    department_name = fields.Char(string='Department')
    school_name = fields.Char(string='School Name',tracking=True)
    school_address_1 = fields.Char(string='School Address 1')
    school_address_2 = fields.Char(string='School Address 2')
    school_address_3 = fields.Char(string='School Address 3')
    post_code = fields.Char(string='Postcode')
    state_id_new = fields.Char(string='State')
    # state_id_new = fields.Many2one('res.country.state', string="State", store=True)
    region_name = fields.Char(string='Region',tracking=True)
    school_type = fields.Char(string = 'School Type')
    curriculum_name = fields.Char(string = 'Curriculum')
    school_group = fields.Char(string='School Group')
    business_history = fields.Date(string='Business History')
    vetted_name = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')],string='Vetted Yes/No')
    product_offered = fields.Char(string='Product Offered')
    board_line_no = fields.Char(string='Board Line No')
    direct_line_no = fields.Char(string='Direct Line no')
    mobile_no = fields.Char(string='Mobile No',tracking=True)
    school_website = fields.Char(string='School/Corporate Website')
    linkedin_profile = fields.Char(string='Contacts Linkedin Profile')
    other_ref_links = fields.Char(string='Other Ref Links')
    label_name = fields.Char(string='Label')
    interest = fields.Char(string='Interest',tracking=True)

    # @api.onchange('country_id')
    # def set_values_to(self):
    #     if self.country_id:
    #         ids = self.env['res.country.state'].search([('country_id', '=', self.country_id_new.id)])
    #         return {
    #             'domain': {'state_id_new': [('id', 'in', ids.ids)],}
    #         }
    