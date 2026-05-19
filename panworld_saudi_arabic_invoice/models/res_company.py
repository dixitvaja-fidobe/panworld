# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import base64
from odoo import api, fields, models, _
from odoo.tools import float_repr
from odoo.exceptions import UserError
import re



class Company(models.Model):
    _inherit = "res.company"

    name = fields.Char(related='partner_id.name', string='Company Name', required=True, store=True, readonly=False, translate=True)
    arabic_address = fields.Text(string='Arabic Address')
    address_arabic = fields.Char(string='Address in Arabic', translate=True)
    add_line_1_ar = fields.Char(translate=True)
    add_line_2_ar = fields.Char(translate=True)
    add_line_3_ar = fields.Char(translate=True)
    add_line_4_ar = fields.Char(translate=True)
    crn_number = fields.Char(string='CRN Number')
    bank_details = fields.Html(string='Bank Details', translate=True)
    bank_details_ar = fields.Html(string='Bank Details Arabic', translate=True)
    payment_term_condition_ar = fields.Html(string='Payment Term Condition (Arabic)', translate=True)

    def to_arabic_text(self, text):
        """
        Converts English text to Arabic script (transliteration).
        No external API, no translation – direct character mapping.
        """

        if not text or not isinstance(text, str):
            return text or ""

        mapping = {
            "a": "ا", "b": "ب", "c": "ك", "d": "د", "e": "ي",
            "f": "ف", "g": "ج", "h": "ه", "i": "ي", "j": "ج",
            "k": "ك", "l": "ل", "m": "م", "n": "ن", "o": "و",
            "p": "ب", "q": "ق", "r": "ر", "s": "س", "t": "ت",
            "u": "و", "v": "ف", "w": "و", "x": "كس", "y": "ي",
            "z": "ز",

            "th": "ث", "sh": "ش", "ch": "تش", "kh": "خ",
            "dh": "ذ", "gh": "غ"
        }

        text = text.lower()

        # Handle digraphs first (th, sh, kh...)
        for eng, ar in sorted(mapping.items(), key=lambda x: -len(x[0])):
            text = re.sub(eng, ar, text)

        return text