# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import os
import logging
from odoo.exceptions import UserError, ValidationError, AccessError
import xlsxwriter
from odoo import _, fields, models, api

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug("Cannot `import xlrd`.")
try:
    import base64
except ImportError:
    _logger.debug("Cannot `import base64`.")


class CostingReport(models.Model):
    _name = "costing.report"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Costing Reports"
    _rec_name = 'name'
    _check_company_auto = True


    def _invoice_default_domain(self):
        domain = [('tracking_number_id', '!=', False), ('move_type', '=', 'out_invoice')]
        return domain


    name = fields.Char()
    date_to = fields.Date('Date To')
    date_from = fields.Date('Date From')
    division_ids = fields.Many2many('division.type',string='Division', relation='division_costing_report_rel')
    partner_ids = fields.Many2many('res.partner', string='Customer', relation='partner_costing_report_rel',)
    cso_reference = fields.Char('COS Reference')
    sale_ids = fields.Many2many('sale.order', string='SO No.', relation='sale_costing_report_rel')
    invoice_ids = fields.Many2many('account.move', string='Invoice No.', relation='invoice_costing_report_rel', domain=_invoice_default_domain)
    salesman_ids = fields.Many2many('res.users')
    # report_type = fields.Selection(selection=[('costing_purchase_report', 'Costing Purchase Report'),
    #     ('costing_average_report', 'Costing Average Report'),], compute="_compute_report_type")

    file_name = fields.Char(string="File Name")
    model_id = fields.Integer(string="Model Id")
    model_name = fields.Char(string="Model Name")

    # company_id = fields.Many2one("res.company")

    #
    # def _compute_report_type(self):
    #     for rec in self:
    #         if self._context.get('costing_average_report'):
    #             rec.report_type = 'costing_average_report'
    #             rec.name = dict(rec._fields['report_type'].selection).get(rec.report_type)
    #         elif self._context.get('costing_purchase_report'):
    #             rec.report_type = 'costing_purchase_report'
    #             rec.name = dict(rec._fields['report_type'].selection).get(rec.report_type)
    #         else:
    #             rec.report_type = ''
    #             rec.name = ''


    # @api.onchange('partner_ids', 'sale_ids', 'invoice_ids', 'date_to', 'date_from','division', 'salesman_ids')
    # def onchange_from_to_date(self):
    #     invoice_domain = []
    #     sale_domain = []
    #     partner_domain = []
    #     if self.partner_ids:
    #         invoice_domain.append(('partner_id', 'in', self.partner_ids.ids))
    #         sale_domain.append(('partner_id', 'in', self.partner_ids.ids))
    #     if self.date_from:
    #         invoice_domain.append(('date', '>=', self.date_from))
    #         sale_domain.append(('date_order', '>=', self.date_from))
    #     if self.date_to:
    #         invoice_domain.append(('date', '<=', self.date_to))
    #         sale_domain.append(('date_order', '<=', self.date_to))
    #     if self.division:
    #         invoice_domain.append(('division_type_id', '=', self.division.id))
    #     if self.salesman_ids:
    #         invoice_domain.append(('invoice_user_id', 'in', self.salesman_ids.ids))
    #     if self.cso_reference:
    #         invoice_domain.append(('tracking_ref', '=', self.cso_reference))
    #         sale_domain.append(('customer_sales_order', '=', self.cso_reference))
    #     if self.invoice_ids:
    #         sale_domain.append(('invoice_ids', 'in', self.invoice_ids._origin.ids))
    #         partner_domain.append(('id', 'in', self.invoice_ids.mapped('partner_id').ids))
    #     sale = self.env['sale.order'].search(sale_domain).ids
    #     partner = self.env['res.partner'].search(partner_domain).ids
    #     if self.sale_ids:
    #         invoices_list = []
    #         # sale_ids = self.sale_ids = self.sale_ids._origin
    #         # invoice_domain.append(('sale_order_ids', 'in', sale_ids.ids))
    #
            # for order in self.sale_ids:
            #     invoices = order.order_line.invoice_lines.move_id.filtered(
            #         lambda r: r.move_type in ('out_invoice', 'out_refund'))
            #     invoices = invoices.search(self._invoice_default_domain() )
            #     invoices_list+= invoices.ids
    #         return {'domain': {'invoice_ids': [('id', 'in', invoices_list)], 'sale_ids': [('id', 'in', sale)]}}
    #     invoice = self.env['account.move'].search([('move_type', '=', 'out_invoice')] + invoice_domain + self._invoice_default_domain()).ids
    #     return {'domain': {'invoice_ids': [('id', 'in', invoice)],
    #                        'sale_ids': [('id', 'in', sale)],
    #                        'partner_ids': [('id', 'in', partner)],
    #                        }}

    # Priya Onchage  For Filters: 18th Jan 2024
    @api.onchange('partner_ids', 'division_ids', 'date_from', 'date_to', 'cso_reference', 'salesman_ids', 'sale_ids', 'invoice_ids')
    def _onchange_fields_filters(self):
        dynamic_domain = []
        sale_domain = []
        partner_domain = []
        salesman_domain = []
        division_domain = []
        if self.partner_ids:
            divisions = self.partner_ids.mapped('division_type_id')
            dynamic_domain.append(('partner_id', 'in', self.partner_ids.ids))
            sale_domain.append(('partner_id', 'in', self.partner_ids.ids))
            division_domain.append(('id', 'in', divisions.ids))
        if self.division_ids:
            dynamic_domain.append(('division_type_id', 'in', self.division_ids.ids))
            partner_domain.append(('division_type_id', 'in', self.division_ids.ids))
        if self.date_from and self.date_to:
            dynamic_domain.append(('date', '>=', self.date_from))
            dynamic_domain.append(('date', '<=', self.date_to))
            sale_domain.append(('date_order', '>=', self.date_from))
            sale_domain.append(('date_order', '<=', self.date_to))
            dynamic_domain.append(('invoice_date', '>=', self.date_from))
            dynamic_domain.append(('invoice_date', '<=', self.date_to))
        if self.cso_reference:
            dynamic_domain.append(('tracking_ref', '=', self.cso_reference))
            sale_domain.append(('customer_sales_order', '=', self.cso_reference))
        if self.sale_ids:
            sale_origins = self.sale_ids.mapped('name')
            partners = self.sale_ids.mapped('partner_id')
            dynamic_domain.append(('invoice_origin', 'in', sale_origins))
            partner_domain.append(('id', 'in', partners.ids))
        if self.salesman_ids:
            dynamic_domain.append(('invoice_user_id', 'in', self.salesman_ids.ids))
        if self.invoice_ids:
            sale_origins = self.invoice_ids.mapped('invoice_origin')
            partners = self.invoice_ids.mapped('partner_id')
            salesmans = self.invoice_ids.mapped('invoice_user_id')
            divisions =  self.invoice_ids.mapped('division_type_id')
            sale_domain.append(('name', 'in', sale_origins))
            partner_domain.append(('id', 'in', partners.ids))
            salesman_domain.append(('id', 'in', salesmans.ids))
            division_domain.append(('id', 'in', divisions.ids))

        # Add common conditions
        dynamic_domain.extend([
            ('tracking_number_id', '!=', False),
            ('move_type', '=', 'out_invoice')
        ])

        sale_domain.extend([('state', '=', 'sale'), ('invoice_ids', '!=', False)])
        return {'domain': {'invoice_ids': dynamic_domain, 'sale_ids': sale_domain, 'partner_ids': partner_domain,
                           'salesman_ids': salesman_domain, 'division_ids': division_domain}}

    #Priya : Load the vlaues on Reload Screen. 18th Jan 2024
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(CostingReport, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                          submenu=submenu)
        if view_type == 'form' and self.env['ir.model.data']._xmlid_to_res_id(
                'costing_reports.view_costing_reports_form') and self._name == 'costing.report':
            costing_average_rec = self.env.ref('costing_reports.costing_average_report_default_data')
            dynamic_domain = []
            sale_domain = []
            partner_domain = []
            salesman_domain = []
            division_domain = []
            partner_ids = costing_average_rec.partner_ids
            division_ids = costing_average_rec.division_ids
            date_from = costing_average_rec.date_from
            date_to = costing_average_rec.date_to
            cso_reference = costing_average_rec.cso_reference
            salesman_ids = costing_average_rec.salesman_ids
            sale_ids = costing_average_rec.sale_ids
            invoice_ids = costing_average_rec.invoice_ids

            if partner_ids:
                divisions = self.partner_ids.mapped('division_type_id')
                dynamic_domain.append(('partner_id', 'in', partner_ids.ids))
                sale_domain.append(('partner_id', 'in', partner_ids.ids))
                division_domain.append(('id', 'in', divisions.ids))
            if division_ids:
                dynamic_domain.append(('division_type_id', 'in', division_ids.ids))
                partner_domain.append(('division_type_id', 'in', division_ids.ids))
            if date_from and date_to:
                dynamic_domain.append(('date', '>=', date_from))
                dynamic_domain.append(('date', '<=', date_to))
                sale_domain.append(('date_order', '>=', date_from))
                sale_domain.append(('date_order', '<=', date_to))
                dynamic_domain.append(('invoice_date', '>=', date_from))
                dynamic_domain.append(('invoice_date', '<=', date_to))
            if cso_reference:
                dynamic_domain.append(('tracking_ref', '=', cso_reference))
                sale_domain.append(('customer_sales_order', '=', cso_reference))
            if sale_ids:
                sale_origins = sale_ids.mapped('name')
                partners = sale_ids.mapped('partner_id')
                dynamic_domain.append(('invoice_origin', 'in', sale_origins))
                partner_domain.append(('id', 'in', partners.ids))
            if salesman_ids:
                dynamic_domain.append(('invoice_user_id', 'in', salesman_ids.ids))
            if invoice_ids:
                sale_origins = invoice_ids.mapped('invoice_origin')
                partners = invoice_ids.mapped('partner_id')
                salesmans = invoice_ids.mapped('invoice_user_id')
                divisions = invoice_ids.mapped('division_type_id')
                sale_domain.append(('name', 'in', sale_origins))
                partner_domain.append(('id', 'in', partners.ids))
                salesman_domain.append(('id', 'in', salesmans.ids))
                division_domain.append(('id', 'in', divisions.ids))

            dynamic_domain.extend([
                ('tracking_number_id', '!=', False),
                ('move_type', '=', 'out_invoice')
            ])
            sale_domain.extend([('state', '=', 'sale'), ('invoice_ids', '!=', False)])

            self.env.context = dict(self.env.context, dynamic_domain=dynamic_domain, sale_domain=sale_domain,
                                    partner_domain=partner_domain, salesman_domain=salesman_domain)
            context = self.env.context or {}
            dynamic_domain = context.get('dynamic_domain', [])
            sale_domain = context.get('sale_domain', [])
            partner_domain = context.get('partner_domain', [])
            salesman_domain = context.get('salesman_domain', [])
            if 'invoice_ids' in result['fields']:
                result['fields']['invoice_ids']['domain'] = dynamic_domain
                result['fields']['sale_ids']['domain'] = sale_domain if sale_domain else self.env['sale.order'].search([('state', '=', 'sale'), ('invoice_ids', '!=', False)]+ sale_domain)
                result['fields']['partner_ids']['domain'] = partner_domain
                result['fields']['salesman_ids']['domain'] = salesman_domain
                result['fields']['division_ids']['domain'] = division_domain
        return result

    @api.constrains('date_from', 'date_to')
    def _constraint_between_start_end_date(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise AccessError(_("To Date must be grater than From Date!"))

    def create_attachment(self, file_name):
        """
        Delete file created in tmp dir, Delete old attachment and create attachment for download report
        :param file_name: file name string
        :return: attachment ir.attachment object
        """
        ir_attachment_obj = self.env['ir.attachment']
        # Read File data
        with open(f'/tmp/{file_name}', "rb+") as file:
            file_data = base64.encodebytes(file.read())
            file.close()

        # Remove tmp file
        os.remove(f'/tmp/{file_name}')
        # Delete Old Attachment
        attachments = ir_attachment_obj.search([('name', '=ilike', file_name)])
        attachments and attachments.unlink()

        return ir_attachment_obj.create({
            'name': file_name,
            'datas': file_data,
            'res_model': 'costing.report',
            'type': 'binary'
        })

    def get_number_formatted(self, value):
        return self.env['ir.qweb.field.float'].value_to_html(value,
                                                             {'thousands_separator': ',',
                                                              'decimal_separator': '.',
                                                              'precision':2})


    def _convert_to_local_currency(self, value, currency):
        company_currency = self.env.company.currency_id

        # Convert amount to company currency
        local_currency_amount = currency._convert(
            value, company_currency, self.env.company, fields.Date.today())

        # Store the result in a computed field or any other field in your model
        return local_currency_amount

    def action_costing_average_report(self):
        """Method to export sample file"""
        file_name = 'costing_average_report.xlsx'
        workbook = xlsxwriter.Workbook(f'/tmp/{file_name}')
        worksheet = workbook.add_worksheet("Costing_Average")
        worksheet.set_landscape()
        # worksheet.protect()
        worksheet.fit_to_pages(1, 0)
        # set zoom size
        worksheet.set_zoom(100)
        # set column width
        for i in range(1, 50):
            worksheet.set_column(i, i, 20)

        border_body = workbook.add_format({'border': 1, 'text_wrap': True})
        header_format = workbook.add_format({'bg_color': 'bababa', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': True})
        light_pink_bg_format_text = workbook.add_format({'bg_color': 'fbe7d9', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': False})
        extra_dark_light_pink_bg_format_text = workbook.add_format({'bg_color': 'f8cbad', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': False})
        sky_blue_bg_format_text = workbook.add_format({'bg_color': 'deebf7', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': False})
        light_blue_bg_format_text = workbook.add_format({'bg_color': 'b4c7e7', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': False})
        light_green_bg_format_header = workbook.add_format({'bg_color': 'a4fc8c', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': True})
        light_green_bg_format_text = workbook.add_format({'bg_color': 'c5e0b4', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': False})
        light_red_bg_format_text = workbook.add_format({'bg_color': 'ff7777', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': False})
        tan_bg_format_text = workbook.add_format({'bg_color': 'fff2cc', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': False})
        yellow_format_header = workbook.add_format({'bg_color': 'ffc000', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': True})
        yellow_format_text = workbook.add_format({'bg_color': 'ffc000', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'bold': False})

        # Set Main Header
        row, col = 1, 0
        worksheet.merge_range(row, col, row, col + 14, '')
        worksheet.merge_range(row, col + 15, row, col + 17, 'Sales Return Adjustment', yellow_format_header)
        worksheet.merge_range(row, col + 18, row, col + 19, 'Landed Cost of Related Sales', yellow_format_header)
        worksheet.merge_range(row, col + 20, row, col + 24, 'Sales Commission', light_green_bg_format_header)
        worksheet.merge_range(row, col + 25, row, col + 30, 'Shipping Outward', yellow_format_header)
        worksheet.merge_range(row, col + 31, row, col + 41, 'Gross Profit Summary', yellow_format_header)

        # Set Header
        row, col = 2, 0
        worksheet.write(row, col, 'Invoice Date', header_format)
        col += 1
        worksheet.write(row, col, 'Invoice No.', header_format)
        col += 1
        worksheet.write(row, col, 'Partner', header_format)
        col += 1
        worksheet.write(row, col, 'Analytical Account', header_format)
        col += 1
        worksheet.write(row, col, 'Division', header_format)
        col += 1
        worksheet.write(row, col, 'Salesman', header_format)
        col += 1
        worksheet.write(row, col, 'Product Code', header_format)
        col += 1
        worksheet.write(row, col, 'Product Name', header_format)
        col += 1
        worksheet.write(row, col, 'Weight_Unit', header_format)
        col += 1
        worksheet.write(row, col, 'S_Qty', header_format)
        col += 1
        worksheet.write(row, col, 'S_List Price', header_format)
        col += 1
        worksheet.write(row, col, 'S_Disc', header_format)
        col += 1
        worksheet.write(row, col, 'S_Unit Price', header_format)
        col += 1
        worksheet.write(row, col, 'G_Sales Value', header_format)
        col += 1
        worksheet.write(row, col, 'Inv_Disc', header_format)
        col += 1
        worksheet.write(row, col, 'CN_No.', header_format)
        col += 1
        worksheet.write(row, col, 'CN_Date', header_format)
        col += 1
        worksheet.write(row, col, 'CN_Qty', header_format)
        col += 1
        worksheet.write(row, col, 'DN_No.', header_format)
        col += 1
        worksheet.write(row, col, 'DN_LCO/Unit', header_format)
        col += 1
        worksheet.write(row, col, 'Sales_Comm (%)', header_format)
        col += 1
        worksheet.write(row, col, 'Other_Comm (%)', header_format)
        col += 1
        worksheet.write(row, col, 'Marketplace cost (%)', header_format)
        col += 1
        worksheet.write(row, col, 'Other cost (%)', header_format)
        col += 1
        worksheet.write(row, col, 'Total_Comm%', header_format)
        col += 1
        worksheet.write(row, col, 'Out_Shipping_Bill NO', header_format)
        col += 1
        worksheet.write(row, col, 'Tracking(AWB)', header_format)
        col += 1
        worksheet.write(row, col, 'Tracking(AWB)_Wt_Kg', header_format)
        col += 1
        worksheet.write(row, col, 'Out_Ship_Bill_Cost', header_format)
        col += 1
        worksheet.write(row, col, 'SHP_Per _kg', header_format)
        col += 1
        worksheet.write(row, col, 'Out_Ship_Cost_Unit', header_format)
        col += 1
        worksheet.write(row, col, 'Total_Sales_Value', header_format)
        col += 1
        worksheet.write(row, col, 'Total_CN_Value', header_format)
        col += 1
        worksheet.write(row, col, 'Net_Sales_Qty', header_format)
        col += 1
        worksheet.write(row, col, 'Net_Sales-Value', header_format)
        col += 1
        worksheet.write(row, col, 'Total_LCO', header_format)
        col += 1
        worksheet.write(row, col, 'LCO_GP', header_format)
        col += 1
        worksheet.write(row, col, 'LCO_GP%', header_format)
        col += 1
        worksheet.write(row, col, 'Total_Comm', header_format)
        col += 1
        worksheet.write(row, col, 'Tot_Out_Ship_Cost', header_format)
        col += 1
        worksheet.write(row, col, 'Final GP', header_format)
        col += 1
        worksheet.write(row, col, 'Final GP%', header_format)

        row = 3

        if not self.invoice_ids:
            # invoices = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('tracking_number_id', '!=', False)])
            dynamic_domain = []
            sale_domain = []
            partner_domain = []
            salesman_domain = []
            division_domain = []
            if self.partner_ids:
                divisions = self.partner_ids.mapped('division_type_id')
                dynamic_domain.append(('partner_id', 'in', self.partner_ids.ids))
                sale_domain.append(('partner_id', 'in', self.partner_ids.ids))
                division_domain.append(('id', 'in', divisions.ids))
            if self.division_ids:
                dynamic_domain.append(('division_type_id', 'in', self.division_ids.ids))
                partner_domain.append(('division_type_id', 'in', self.division_ids.ids))
            if self.date_from and self.date_to:
                dynamic_domain.append(('date', '>=', self.date_from))
                dynamic_domain.append(('date', '<=', self.date_to))
                sale_domain.append(('date_order', '>=', self.date_from))
                sale_domain.append(('date_order', '<=', self.date_to))
                dynamic_domain.append(('invoice_date', '>=', self.date_from))
                dynamic_domain.append(('invoice_date', '<=', self.date_to))
            if self.cso_reference:
                dynamic_domain.append(('tracking_ref', '=', self.cso_reference))
                sale_domain.append(('customer_sales_order', '=', self.cso_reference))
            if self.sale_ids:
                sale_origins = self.sale_ids.mapped('name')
                partners = self.sale_ids.mapped('partner_id')
                dynamic_domain.append(('invoice_origin', 'in', sale_origins))
                partner_domain.append(('id', 'in', partners.ids))
            if self.salesman_ids:
                dynamic_domain.append(('invoice_user_id', 'in', self.salesman_ids.ids))
            if self.invoice_ids:
                sale_origins = self.invoice_ids.mapped('invoice_origin')
                partners = self.invoice_ids.mapped('partner_id')
                salesmans = self.invoice_ids.mapped('invoice_user_id')
                divisions = self.invoice_ids.mapped('division_type_id')
                sale_domain.append(('name', 'in', sale_origins))
                partner_domain.append(('id', 'in', partners.ids))
                salesman_domain.append(('id', 'in', salesmans.ids))
                division_domain.append(('id', 'in', divisions.ids))

            # Add common conditions
            dynamic_domain.extend([
                ('tracking_number_id', '!=', False),
                ('move_type', '=', 'out_invoice')
            ])

            invoices = self.env['account.move'].search(dynamic_domain)
        else:
            invoices = self.invoice_ids

        total_so_qty = total_price_subtotal = total_inv_disc = total_prd_quantity = all_total_sales_value = all_total_cn_value = total_net_sales_qty = total_net_sales_value = all_total_lCO = total_LCO_GP = all_total_Comm = all_Tot_Out_Ship_Cost = total_Final_GP = 0.0

        for line in invoices.mapped('invoice_line_ids').filtered(lambda l : l.product_id.is_discount_product != True):
            picking_id = line.move_id.picking_ids[0] if line.move_id.picking_ids else None
            cn_id = self.env['account.move'].search([('move_type', '=', 'out_refund'),('related_invoice_id', '=', line.move_id.id)])
            # picking_id = line.sale_line_ids[:1].order_id.picking_ids[:1]
            marketplace_cost_ids = line.move_id.partner_id.marketplace_cost_ids
            salesman_commission = sum(marketplace_cost_ids.mapped('salesman_commission'))
            other_commission = sum(marketplace_cost_ids.mapped('other_commission'))
            col = 0
            date_object = line.move_id.date
            formatted_date = date_object.strftime('%Y-%m-%d')
            total_so_qty += line.quantity
            total_price_subtotal += line.price_subtotal

            worksheet.write(row, col, formatted_date or '', border_body) #invoice date
            col += 1
            worksheet.write(row, col, line.move_id.name or '', border_body) #invoice no
            col += 1
            worksheet.write(row, col, line.move_id.partner_id.name or '', border_body) #partner
            col += 1
            worksheet.write(row, col, line.move_id.analytic_account_id.name or '', border_body) #Analytical Account
            col += 1
            worksheet.write(row, col, line.move_id.division_type_id.name or '', border_body) #Division
            col += 1
            worksheet.write(row, col, line.move_id.invoice_user_id.name or '', border_body) #Salesman
            col += 1
            worksheet.write(row, col, line.product_id.default_code or '', border_body)  #product code
            col += 1
            worksheet.write(row, col, line.product_id.name or '', border_body)  #product name
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.product_id.weight) or 0.0, light_pink_bg_format_text)  #Weight_Unit
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.quantity) or 0.0, light_pink_bg_format_text)  # S_Qty
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.price_unit) or 0.0, light_pink_bg_format_text)  # S_List Price
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.discount) or 0.0, light_pink_bg_format_text)  # S_Disc
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.list_price) or 0.0, light_pink_bg_format_text)  # S_Unit Price
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.price_subtotal) or 0.0, light_pink_bg_format_text)  # G_Sales Value
            col += 1

            #Invocie discount formula
            obj_line = invoices.mapped('invoice_line_ids').filtered(lambda l: l.move_id.id == line.move_id.id)
            inv_disc = 0
            disc_amount = sum(obj_line.filtered(lambda l: l.product_id.is_discount_product).mapped('price_subtotal'))
            if disc_amount:
                product_sum_amount = sum(obj_line.filtered(lambda l: not l.product_id.is_discount_product).mapped(
                    'price_subtotal'))
                inv_disc = (disc_amount/product_sum_amount) * (line.price_subtotal) or 0
                inv_disc = round(inv_disc, 2)

            worksheet.write(row, col, self.get_number_formatted(inv_disc), light_pink_bg_format_text)  # Inv_Disc
            total_inv_disc += inv_disc
            col += 1
            worksheet.write(row, col, cn_id.name if cn_id else None, sky_blue_bg_format_text)  # CN_No.
            col += 1

            formatted_cn_date = cn_id.date.strftime('%Y-%m-%d') if cn_id else None
            worksheet.write(row, col, formatted_cn_date or None, sky_blue_bg_format_text)  # CN_Date
            col += 1
            prd_id = cn_id.invoice_line_ids.filtered(lambda l: l.product_id == line.product_id)
            worksheet.write(row, col, self.get_number_formatted(prd_id.quantity) or None, sky_blue_bg_format_text)  # CN_Qty if cn
            total_prd_quantity += prd_id.quantity
            col += 1
            worksheet.write(row, col, picking_id.name if picking_id else '', tan_bg_format_text)  # DN_No.
            col += 1
            cost_value = picking_id.move_ids.mapped('stock_valuation_layer_ids').filtered(lambda s: s.product_id == line.product_id).unit_cost if picking_id else False
            worksheet.write(row, col, self.get_number_formatted(cost_value), tan_bg_format_text)  # DN_LCO/Unit
            col += 1
            worksheet.write(row, col, self.get_number_formatted(sum(marketplace_cost_ids.mapped('salesman_commission'))),light_green_bg_format_text)  #Sales_Comm (%)
            col += 1
            worksheet.write(row, col, self.get_number_formatted(sum(marketplace_cost_ids.mapped('other_commission'))), light_green_bg_format_text)  # Other_Comm (%)
            col += 1
            worksheet.write(row, col, self.get_number_formatted(sum(marketplace_cost_ids.mapped('marketplace_cost'))), light_green_bg_format_text)  # Marketplace cost (%)
            col += 1
            worksheet.write(row, col, self.get_number_formatted(sum(marketplace_cost_ids.mapped('other_cost'))), light_green_bg_format_text)  # Other cost (%)
            col += 1
            Total_Comm_percentage = sum(marketplace_cost_ids.mapped('salesman_commission')) + sum(marketplace_cost_ids.mapped('other_cost')) + sum(marketplace_cost_ids.mapped('other_commission')) + sum(marketplace_cost_ids.mapped('marketplace_cost'))
            worksheet.write(row, col, self.get_number_formatted(Total_Comm_percentage) or '', light_green_bg_format_text)  # Total_Comm%
            col += 1

            Out_Shipping_Bill_no = self.env['account.move.line'].search(
                [('move_id.is_shipping_service', '=', True),
                 ('bill_tracking_number_id', '=', line.tracking_number_id.id)]).move_id.mapped('name')

            journal_Out_Shipping_Bill_no = self.env['account.move.line'].search(
                [('journal_tracking_number_id', '=', line.tracking_number_id.id)]).move_id.mapped('name')

            Out_Shipping_Bill_no = Out_Shipping_Bill_no + journal_Out_Shipping_Bill_no if journal_Out_Shipping_Bill_no else Out_Shipping_Bill_no

            value_text = ''
            values_list = list(dict.fromkeys(Out_Shipping_Bill_no))
            total_shipping_cost = line.tracking_number_id.cost + line.tracking_number_id.total_debit_amount
            for rec in Out_Shipping_Bill_no:
                if values_list[0] == rec:
                    value_text += rec
                else:
                    value_text += ',' + rec
            worksheet.write(row, col, value_text, extra_dark_light_pink_bg_format_text)  # Out_Shipping_Bill NO
            col += 1
            worksheet.write(row, col, line.tracking_number_id.name, extra_dark_light_pink_bg_format_text)  # Tracking(AWB)
            col += 1
            Wt_Kg = sum(line.tracking_number_id.mapped('invoice_line_ids').mapped('weight_qty'))
            worksheet.write(row, col, self.get_number_formatted(round(Wt_Kg, 2)) or 0.0, extra_dark_light_pink_bg_format_text)  # Tracking(AWB)_Wt_Kg
            col += 1

            worksheet.write(row, col, self.get_number_formatted(round(total_shipping_cost, 2)) or 0.0, extra_dark_light_pink_bg_format_text)  # Out_Ship_Bill_Cost
            col += 1
            # SHP_Per_product = line.tracking_number_id.mapped('invoice_line_ids').filtered(lambda t: t.id == line.id).shipping_cost_per_product

            SHP_Per_product = total_shipping_cost / Wt_Kg if Wt_Kg > 0 else 0
            worksheet.write(row, col, self.get_number_formatted(round(SHP_Per_product, 2)) or 0.0, extra_dark_light_pink_bg_format_text)  # SHP_Per _kg
            col += 1
            Out_Ship_Cost_Unit = SHP_Per_product * line.product_id.weight if line.product_id.weight else 0
            worksheet.write(row, col, self.get_number_formatted(round(Out_Ship_Cost_Unit, 2)) or 0.0, extra_dark_light_pink_bg_format_text)  # Out_Ship_Cost_Unit
            col += 1

            Total_Sales_Value = line.price_subtotal - inv_disc
            worksheet.write(row, col, self.get_number_formatted(round(Total_Sales_Value, 2)) or 0.0, light_green_bg_format_text)  # Total_Sales_Value
            all_total_sales_value += Total_Sales_Value
            col += 1

            Total_CN_Value = (Total_Sales_Value/line.quantity) * prd_id.quantity if line.quantity > 0 else 0
            worksheet.write(row, col, self.get_number_formatted(round(Total_CN_Value, 2)) or 0.0, light_green_bg_format_text)  # Total_CN_Value
            all_total_cn_value += Total_CN_Value
            col += 1
            Net_Sales_Qty = line.quantity - prd_id.quantity
            worksheet.write(row, col, self.get_number_formatted(round(Net_Sales_Qty, 2)) or 0.0, light_green_bg_format_text)  # Net_Sales_Qty
            total_net_sales_qty += Net_Sales_Qty
            col += 1
            Net_Sales_value = Total_Sales_Value - Total_CN_Value
            worksheet.write(row, col, self.get_number_formatted(round(Net_Sales_value, 2)) or 0, light_green_bg_format_text)  # Net_Sales-Value
            total_net_sales_value += Net_Sales_value
            col += 1
            Total_LCO = (cost_value or 0) * (Net_Sales_Qty or 0)
            worksheet.write(row, col, self.get_number_formatted(round(Total_LCO, 2)) or 0.0, light_green_bg_format_text)  # Total_LCO
            all_total_lCO += Total_LCO
            col += 1
            LCO_GP = Net_Sales_value - Total_LCO
            worksheet.write(row, col, self.get_number_formatted(round(LCO_GP, 2)) or 0.0, extra_dark_light_pink_bg_format_text)  # LCO_GP
            total_LCO_GP += LCO_GP
            col += 1
            LCO_GP_percentage = (LCO_GP/Net_Sales_value) *100 if Net_Sales_value > 0 else 0
            worksheet.write(row, col, self.get_number_formatted(round(LCO_GP_percentage, 2)) or 0.0, extra_dark_light_pink_bg_format_text)  # LCO_GP%
            col += 1
            Total_Comm = (Net_Sales_value*Total_Comm_percentage)/100
            worksheet.write(row, col, self.get_number_formatted(round(Total_Comm, 2)) or 0.0, light_blue_bg_format_text)  # Total_Comm
            all_total_Comm += Total_Comm
            col += 1
            Tot_Out_Ship_Cost = Out_Ship_Cost_Unit * line.quantity
            worksheet.write(row, col, self.get_number_formatted(round(Tot_Out_Ship_Cost, 2)) or 0.0, light_blue_bg_format_text)  # Tot_Out_Ship_Cost
            all_Tot_Out_Ship_Cost += Tot_Out_Ship_Cost
            col += 1
            Final_GP = LCO_GP - Total_Comm - Tot_Out_Ship_Cost
            worksheet.write(row, col, self.get_number_formatted(round(Final_GP, 2)) or 0.0, light_blue_bg_format_text)  # Final GP
            total_Final_GP += Final_GP
            col += 1
            Final_GP_percentage = (Final_GP/Net_Sales_value) * 100 if Net_Sales_value > 0 else 0
            worksheet.write(row, col, self.get_number_formatted(round(Final_GP_percentage, 2)) or 0.0, light_blue_bg_format_text)  # Final GP%
            col += 1

            row +=1

        worksheet.merge_range(row, 0, row, 6, ' ', border_body)
        col += 1
        worksheet.write(row, 7, 'Total', header_format)
        col +=1
        worksheet.write(row, 8, ' ', header_format)
        col += 1
        worksheet.write(row, 9, self.get_number_formatted(total_so_qty) or 0.0, header_format)
        col += 1
        worksheet.write(row, 10, ' ', header_format)
        col += 1
        worksheet.write(row, 11, ' ', header_format)
        col += 1
        worksheet.write(row, 12, ' ', header_format)
        col += 1
        worksheet.write(row, 13, self.get_number_formatted(total_price_subtotal) or 0.0, header_format)
        col += 1
        worksheet.write(row, 14, self.get_number_formatted(total_inv_disc) or 0.0, header_format)
        col += 1
        worksheet.write(row, 15, ' ', header_format)
        col += 1
        worksheet.write(row, 16, ' ', header_format)
        col += 1
        worksheet.write(row, 17, self.get_number_formatted(total_prd_quantity) or 0.0, header_format)
        col += 1
        worksheet.write(row, 18, ' ', header_format)
        col += 1
        worksheet.write(row, 19, ' ', header_format)
        col += 1
        worksheet.write(row, 20, ' ', header_format)
        col += 1
        worksheet.write(row, 21, ' ', header_format)
        col += 1
        worksheet.write(row, 22, ' ', header_format)
        col += 1
        worksheet.write(row, 23, ' ', header_format)
        col += 1
        worksheet.write(row, 24, ' ', header_format)
        col += 1
        worksheet.write(row, 25, ' ', header_format)
        col += 1
        worksheet.write(row, 26, ' ', header_format)
        col += 1
        worksheet.write(row, 27, ' ', header_format)
        col += 1
        worksheet.write(row, 28, ' ', header_format)
        col += 1
        worksheet.write(row, 29, ' ', header_format)
        col += 1
        worksheet.write(row, 30, ' ', header_format)
        col += 1
        worksheet.write(row, 31, self.get_number_formatted(all_total_sales_value) or 0.0, header_format)
        col += 1
        worksheet.write(row, 32, self.get_number_formatted(all_total_cn_value) or 0.0, header_format)
        col += 1
        worksheet.write(row, 33, self.get_number_formatted(total_net_sales_qty) or 0.0, header_format)
        col += 1
        worksheet.write(row, 34, self.get_number_formatted(total_net_sales_value) or 0.0, header_format)
        col += 1
        worksheet.write(row, 35, self.get_number_formatted(all_total_lCO) or 0.0, header_format)
        col += 1
        worksheet.write(row, 36, self.get_number_formatted(total_LCO_GP) or 0.0, header_format)
        col += 1
        total_LCO_GP_per = (total_LCO_GP / total_net_sales_qty) * 100 if total_net_sales_qty else 0.0
        worksheet.write(row, 37, self.get_number_formatted(total_LCO_GP_per), header_format)
        col += 1
        worksheet.write(row, 38, self.get_number_formatted(all_total_Comm) or 0.0, header_format)
        col += 1
        worksheet.write(row, 39, self.get_number_formatted(all_Tot_Out_Ship_Cost) or 0.0, header_format)
        col += 1
        worksheet.write(row, 40, self.get_number_formatted(total_Final_GP) or 0.0, header_format)
        col += 1
        total_Final_GP_per = (total_Final_GP / total_net_sales_qty) * 100 if total_net_sales_qty else 0.0
        worksheet.write(row, 41,  self.get_number_formatted(total_Final_GP_per) or 0.0, header_format)

        worksheet.freeze_panes(0, 8)
        worksheet.hide_gridlines(option=2)
        # close file
        workbook.close()
        # Create Attachment
        attachment = self.create_attachment(file_name)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def action_costing_purchase_report(self):
        """Method to export sample file"""
        file_name = 'Costing Purchase.xlsx'
        workbook = xlsxwriter.Workbook(f'/tmp/{file_name}')
        worksheet = workbook.add_worksheet("Costing_Purchase")
        worksheet.set_landscape()
        # worksheet.protect()
        worksheet.fit_to_pages(1, 0)
        # set zoom size
        worksheet.set_zoom(100)
        # set column width
        for i in range(1, 55):
            worksheet.set_column(i, i, 20)

        header_format = workbook.add_format({'bg_color':'D3D3D3','align': 'center', 'valign': 'vcenter', 'bold': True, 'border': 1})
        light_pink_bg_format = workbook.add_format(
            {'bg_color': 'ffa1ff', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'border': 1})
        sky_blue_bg_format = workbook.add_format(
            {'bg_color': 'a1aeff', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'border': 1})
        light_blue_bg_format = workbook.add_format(
            {'bg_color': '415bfb', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'border': 1})
        light_green_bg_format = workbook.add_format(
            {'bg_color': 'a4fc8c', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'border': 1})
        light_red_bg_format = workbook.add_format(
            {'bg_color': 'ff7777', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'border': 1})
        tan_bg_format = workbook.add_format(
            {'bg_color': 'fcb28c', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'bold': True, 'border': 1})
        yellow_format_header = workbook.add_format(
            {'bg_color': 'ffc000', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'border': 1,
             'bold': True})
        border_body = workbook.add_format({'border': 1,  'text_wrap': True})
        light_skin_body = workbook.add_format({'bg_color': 'ffe0bd', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        light_blue_body = workbook.add_format({'bg_color': 'A9CEEA', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        light_yellow_body = workbook.add_format({'bg_color': 'FFECB7', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        dark_skin_body = workbook.add_format({'bg_color': 'F6C795', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        dark_blue_body = workbook.add_format({'bg_color': '6fa8dc', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        dark_green_body = workbook.add_format({'bg_color': '9DC98A', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        light_green_body = workbook.add_format({'bg_color': 'D2FFBE', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})

        # Set Main Header
        row, col = 1, 0
        worksheet.merge_range(row, col, row, col + 14, '')
        worksheet.merge_range(row, col + 15, row, col + 17, 'Sales Return Adjustment', yellow_format_header)
        worksheet.merge_range(row, col + 18, row, col + 21, 'Purchase Cost of Related Sales', yellow_format_header)
        worksheet.merge_range(row, col + 22, row, col + 27, 'Shipping Inward Cost', yellow_format_header)
        worksheet.merge_range(row, col + 28, row, col + 32, 'Sales Commissions', light_green_bg_format)
        worksheet.merge_range(row, col + 33, row, col + 38, 'Freight Outward', yellow_format_header)
        worksheet.merge_range(row, col + 39, row, col + 52, 'Gross Profit Summary', yellow_format_header)

        # Set Header
        row, col = 2, 0
        worksheet.write(row, col, 'Invocie Date', header_format)
        col += 1
        worksheet.write(row, col, 'Invoice No.', header_format)
        col += 1
        worksheet.write(row, col, 'Partner', header_format)
        col += 1
        worksheet.write(row, col, 'Analytical Account', header_format)
        col += 1
        worksheet.write(row, col, 'Division', header_format)
        col += 1
        worksheet.write(row, col, 'Salesman', header_format)
        col += 1
        worksheet.write(row, col, 'Product Code', header_format)
        col += 1
        worksheet.write(row, col, 'Product Name', header_format)
        col += 1
        worksheet.write(row, col, 'Weight_Unit', header_format)
        col += 1
        worksheet.write(row, col, 'S_Qty', header_format)
        col += 1
        worksheet.write(row, col, 'S_List Price', header_format)
        col += 1
        worksheet.write(row, col, 'S_Disc', header_format)
        col += 1
        worksheet.write(row, col, 'S_Unit Price', header_format)
        col += 1
        worksheet.write(row, col, 'G_Sales Value', header_format)
        col += 1
        worksheet.write(row, col, 'Inv_Disc', header_format)
        col += 1
        worksheet.write(row, col, 'CN_No.', header_format)
        col += 1
        worksheet.write(row, col, 'CN_Date', header_format)
        col += 1
        worksheet.write(row, col, 'CN_Qty', header_format)
        col += 1
        worksheet.write(row, col, 'PO No.', header_format)
        col += 1
        worksheet.write(row, col, 'Bill_List_Price', header_format)
        col += 1
        worksheet.write(row, col, 'Bill_Disc', header_format)
        col += 1
        worksheet.write(row, col, 'Bill_Unit_Price', header_format)
        col += 1
        worksheet.write(row, col, 'Out_Shipping_Bill NO', header_format)
        col += 1
        worksheet.write(row, col, 'Tracking(AWB)', header_format)
        col += 1
        worksheet.write(row, col, 'Tracking(AWB)_Wt_Kg', header_format)
        col += 1
        worksheet.write(row, col, 'In_Ship_Bill_Cost', header_format)
        col += 1
        worksheet.write(row, col, 'SHP_Per_kg', header_format)
        col += 1
        worksheet.write(row, col, 'In_Ship_Cost_Unit', header_format)
        col += 1
        worksheet.write(row, col, 'Sales_Comm (%)', header_format)
        col += 1
        worksheet.write(row, col, 'Other_Comm (%)', header_format)
        col += 1
        worksheet.write(row, col, 'Marketplace cost (%)', header_format)
        col += 1
        worksheet.write(row, col, 'Other cost (%)', header_format)
        col += 1
        worksheet.write(row, col, 'Total_Comm%', header_format)
        col += 1
        worksheet.write(row, col, 'Out_Shipping_Doc', header_format)
        col += 1
        worksheet.write(row, col, 'Tracking(AWB)', header_format)
        col += 1
        worksheet.write(row, col, 'Tracking(AWB)_Wt_Kg', header_format)
        col += 1
        worksheet.write(row, col, 'Out_Ship_Bill_Cost', header_format)
        col += 1
        worksheet.write(row, col, 'SHP_Per _kg', header_format)
        col += 1
        worksheet.write(row, col, 'Out_Ship_Cost_Unit', header_format)
        col += 1
        worksheet.write(row, col, 'Total_Sales_Value', header_format)
        col += 1
        worksheet.write(row, col, 'Total_CN_Value', header_format)
        col += 1
        worksheet.write(row, col, 'Net_Sales_Qty', header_format)
        col += 1
        worksheet.write(row, col, 'Net_Sales-Value', header_format)
        col += 1
        worksheet.write(row, col, 'Total_Mat_Cost', header_format)
        col += 1
        worksheet.write(row, col, 'Contribution_Mat', header_format)
        col += 1
        worksheet.write(row, col, 'Mat_Contr_GP1%', header_format)
        col += 1
        worksheet.write(row, col, 'In_Shipping_Cost', header_format)
        col += 1
        worksheet.write(row, col, 'LCO_GP', header_format)
        col += 1
        worksheet.write(row, col, 'LCO_GP%', header_format)
        col += 1
        worksheet.write(row, col, 'Total_Comm', header_format)
        col += 1
        worksheet.write(row, col, 'Tot_Out_Ship_Cost', header_format)
        col += 1
        worksheet.write(row, col, 'Final GP', header_format)
        col += 1
        worksheet.write(row, col, 'Final GP%', header_format)

        row = 3
        if not self.invoice_ids:
            # invoices = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('tracking_number_id', '!=', False)])
            dynamic_domain = []
            sale_domain = []
            partner_domain = []
            salesman_domain = []
            division_domain = []
            if self.partner_ids:
                divisions = self.partner_ids.mapped('division_type_id')
                dynamic_domain.append(('partner_id', 'in', self.partner_ids.ids))
                sale_domain.append(('partner_id', 'in', self.partner_ids.ids))
                division_domain.append(('id', 'in', divisions.ids))
            if self.division_ids:
                dynamic_domain.append(('division_type_id', 'in', self.division_ids.ids))
                partner_domain.append(('division_type_id', 'in', self.division_ids.ids))
            if self.date_from and self.date_to:
                dynamic_domain.append(('date', '>=', self.date_from))
                dynamic_domain.append(('date', '<=', self.date_to))
                sale_domain.append(('date_order', '>=', self.date_from))
                sale_domain.append(('date_order', '<=', self.date_to))
                dynamic_domain.append(('invoice_date', '>=', self.date_from))
                dynamic_domain.append(('invoice_date', '<=', self.date_to))
            if self.cso_reference:
                dynamic_domain.append(('tracking_ref', '=', self.cso_reference))
                sale_domain.append(('customer_sales_order', '=', self.cso_reference))
            if self.sale_ids:
                sale_origins = self.sale_ids.mapped('name')
                partners = self.sale_ids.mapped('partner_id')
                dynamic_domain.append(('invoice_origin', 'in', sale_origins))
                partner_domain.append(('id', 'in', partners.ids))
            if self.salesman_ids:
                dynamic_domain.append(('invoice_user_id', 'in', self.salesman_ids.ids))
            if self.invoice_ids:
                sale_origins = self.invoice_ids.mapped('invoice_origin')
                partners = self.invoice_ids.mapped('partner_id')
                salesmans = self.invoice_ids.mapped('invoice_user_id')
                divisions = self.invoice_ids.mapped('division_type_id')
                sale_domain.append(('name', 'in', sale_origins))
                partner_domain.append(('id', 'in', partners.ids))
                salesman_domain.append(('id', 'in', salesmans.ids))
                division_domain.append(('id', 'in', divisions.ids))

            # Add common conditions
            dynamic_domain.extend([
                ('tracking_number_id', '!=', False),
                ('move_type', '=', 'out_invoice')
            ])

            invoices = self.env['account.move'].search(dynamic_domain)

        else:
            invoices = self.invoice_ids

        if self.date_from and self.date_to:
            invoices = invoices.filtered(lambda x: x.invoice_date >= self.date_from and x.invoice_date <= self.date_to)

        costing_po_total_so_qty = costing_po_total_price_subtotal = costing_po_total_inv_disc = costing_total_prd_quantity = costing_all_total_sales_value = 0.0
        costing_all_total_cn_value = costing_total_net_sales_qty = costing_total_net_sales_value = costing_Total_Mat_Cost = costing_contribution_mat = 0.0
        costing_in_shipping_costt = costing_lco_gp = costing_total_comm = costing_tot_out_ship_cost = costing_final_gp = 0.0


        product_weight = 0.0
        inv_disc_list = []
        #for line in self.invoice_ids.mapped('invoice_line_ids'):
        for line in invoices.mapped('invoice_line_ids').filtered(lambda l: l.product_id.is_discount_product != True):
            # picking_id = line.move_id.picking_ids[0] if line.move_id.picking_ids else None
            # cn_id = self.env['account.move'].search(
            #     [('rma_id', '=', line.move_id.rma_id.id), ('move_type', '=', 'out_refund')]) if line.move_id.rma_id else None

            cn_id = self.env['account.move'].search([('move_type', '=', 'out_refund'),('related_invoice_id', '=', line.move_id.id)])

            #invoice disount
            obj_line = invoices.mapped('invoice_line_ids').filtered(lambda l: l.move_id.id == line.move_id.id)
            inv_disc = 0
            disc_amount = sum(obj_line.filtered(lambda l: l.product_id.is_discount_product).mapped('price_subtotal'))
            if disc_amount:
                product_sum_amount = sum(obj_line.filtered(lambda l: not l.product_id.is_discount_product).mapped(
                    'price_subtotal'))
                inv_disc = (disc_amount / product_sum_amount) * (
                            line.price_subtotal ) or 0
                inv_disc = round(inv_disc, 2)

            # inv_disc_list.append(line.price_subtotal)
            # inv_disc = 60 / sum(inv_disc_list) * line.price_subtotal
            col = 0
            date_object = line.move_id.date
            formatted_date = date_object.strftime('%Y-%m-%d')
            costing_po_total_so_qty += line.quantity
            costing_po_total_price_subtotal += line.price_subtotal

            worksheet.write(row, col, formatted_date or '', border_body)  # invoice date
            col += 1
            worksheet.write(row, col, line.move_id.name or '', border_body)  # invoice no
            col += 1
            worksheet.write(row, col, line.move_id.partner_id.name or '', border_body)  # partner
            col += 1
            worksheet.write(row, col, line.move_id.analytic_account_id.name or '', border_body)  # Analytical Account
            col += 1
            worksheet.write(row, col, line.move_id.division_type_id.name or '', border_body)  # Division
            col += 1
            worksheet.write(row, col, line.move_id.invoice_user_id.name or '', border_body)  # Salesman
            col += 1
            worksheet.write(row, col, line.product_id.default_code or '', border_body)  # product code
            col += 1
            worksheet.write(row, col, line.product_id.name or '', border_body)  # product name
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.product_id.weight) or 0.0, light_skin_body)  # Weight_Unit
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.quantity) or 0.0, light_skin_body)  # S_Qty
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.price_unit) or 0.0, light_skin_body)  # S_List Price
            col += 1
            worksheet.write(row, col, round(line.discount, 2) or 0.0, light_skin_body)  # S_Disc
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.list_price) or 0.0, light_skin_body)  # S_Unit Price
            col += 1
            worksheet.write(row, col, self.get_number_formatted(line.price_subtotal) or 0.0, light_skin_body)  # G_Sales Value
            col += 1
            worksheet.write(row, col, self.get_number_formatted(inv_disc) or '', light_skin_body)  # Inv_Disc
            costing_po_total_inv_disc += inv_disc
            col += 1
            worksheet.write(row, col, cn_id.name if cn_id else '', light_blue_body)  # CN_No.
            col += 1

            total_shipping_cost = line.tracking_number_id.cost + line.tracking_number_id.total_debit_amount
            formatted_cn_date = cn_id.date.strftime('%Y-%m-%d') if cn_id else None
            worksheet.write(row, col, formatted_cn_date if cn_id else '', light_blue_body)  # CN_Date
            col += 1
            if cn_id:
                prd_id = cn_id.invoice_line_ids.filtered(lambda l: l.product_id == line.product_id)
                worksheet.write(row, col, self.get_number_formatted(prd_id.quantity) or 0.0, light_blue_body)  # CN_Qty if cn
                costing_total_prd_quantity += prd_id.quantity
            else:
                worksheet.write(row, col, '', light_blue_body)  # CN_Qty

            col += 1
            po_no = self.env['purchase.order.line'].filtered(lambda l: l.product_id == line.product_id).search(
                [('related_so', '=', line.sale_line_ids.order_id.id)]) if line.sale_line_ids.order_id.name else None
            if po_no and len(po_no.mapped('order_id')) > 1:
                po_no = po_no.filtered(lambda l: l.order_id == po_no.mapped('order_id')[0])
            worksheet.write(row, col, po_no.order_id.name if po_no else '', light_yellow_body)  # PO No.
            col += 1
            Bill_List_Price = 0.0
            if po_no:
                Bill_List_Price = self._convert_to_local_currency(po_no.filtered(lambda l: l.product_id == line.product_id).list_price, currency=po_no.order_id.currency_id)
            worksheet.write(row, col, self.get_number_formatted(Bill_List_Price) if po_no else '', light_yellow_body)  # Bill_List_Price
                    #self.get_number_formatted(po_no.filtered(lambda l: l.product_id == line.product_id).list_price)
            col += 1
            worksheet.write(row, col, self.get_number_formatted(po_no.filtered(lambda l: l.product_id == line.product_id).discount) if po_no else '', light_yellow_body)  # Bill_Disc
            col += 1
            Bill_Unit_Price = 0.0
            if po_no:
                Bill_Unit_Price = self._convert_to_local_currency(po_no.filtered(lambda l: l.product_id == line.product_id).price_unit, currency=po_no.order_id.currency_id)
            worksheet.write(row, col, self.get_number_formatted(Bill_Unit_Price) if po_no else '', light_yellow_body)  # Bill_Unit_Price
            col += 1
            move_line_ids = self.env['account.move.line']
            if line.tracking_number_id:
                move_line_ids = self.env['account.move.line'].search(
                    [('move_id.is_shipping_service', '=', True),
                     ('bill_tracking_number_id', '=', line.tracking_number_id.id)])

                # move_line_ids += self.env['account.move.line'].search(
                #     [('journal_tracking_number_id', '=', line.tracking_number_id.id)])

                journal_line_ids = self.env['account.move.line'].search([('journal_tracking_number_id', '=', line.tracking_number_id.id)])

                move_line_ids = move_line_ids + journal_line_ids if journal_line_ids else move_line_ids
            if move_line_ids:
                account_ids_query = ', '.join(str(line_id.move_id.name)
                                              for line_id in move_line_ids)
            else:
                account_ids_query = ''

            account_in_bill = ''
            bill_tracking_no = ''
            bill_line_ids = ''
            if po_no:
                bill_tracking_no = self.env['account.move'].search([('move_type', '=', 'in_invoice'),
                                                                    ('invoice_origin', '=', po_no.order_id.name)])
                bill_line_ids = self.env['account.move.line'].search(
                    [('bill_tracking_number_id', '=', bill_tracking_no.tracking_number_bill_id.id),
                     ('move_id.is_shipping_service', '=', True),
                     ]) if bill_tracking_no.tracking_number_bill_id else None
                bill_journal_line_ids = self.env['account.move.line'].search(
                    [('journal_tracking_number_id', '=', bill_tracking_no.tracking_number_bill_id.id)]) if bill_tracking_no.tracking_number_bill_id else None

                all_bill_line_ids = bill_line_ids + bill_journal_line_ids if bill_journal_line_ids else bill_line_ids
                account_in_bill = ', '.join(str(line_id.move_id.name)
                                              for line_id in all_bill_line_ids) if all_bill_line_ids else None

            worksheet.write(row, col, account_in_bill if account_in_bill else '', dark_skin_body)  # Out_Shipping_Bill NO
            col += 1
            worksheet.write(row, col, bill_tracking_no.tracking_number_bill_id.name if bill_tracking_no else '', dark_skin_body)  # Tracking(AWB)
            col += 1
            weight = []
            if bill_line_ids:
                for rec in bill_line_ids:
                    weight = rec.bill_tracking_number_id.mapped('bill_line_ids').mapped('weight_qty')
            total_bill_shipping_cost = bill_tracking_no.tracking_number_bill_id.cost + bill_tracking_no.tracking_number_bill_id.total_debit_amount if bill_tracking_no else 0.0
            worksheet.write(row, col, self.get_number_formatted(sum(weight)) or '', dark_skin_body)  # Tracking(AWB)_Wt_Kg
            col += 1
            worksheet.write(row, col, self.get_number_formatted(total_bill_shipping_cost) if bill_tracking_no else 0.0 or '' , dark_skin_body)  # In_Ship_Bill_Cost
            col += 1
            SHP_Per_kg = total_bill_shipping_cost / sum(weight) if sum(weight) and bill_tracking_no else 0
            worksheet.write(row, col, self.get_number_formatted(round(SHP_Per_kg,2)) or 0.0, dark_skin_body)  # SHP_Per _kg
            col += 1

            In_Ship_Cost_Unit = (SHP_Per_kg * line.product_id.weight) or 0
            worksheet.write(row, col, self.get_number_formatted(round(In_Ship_Cost_Unit, 2)) or 0.0, dark_skin_body)  # In_Ship_Cost_Unit
            col += 1
            worksheet.write(row, col, self.get_number_formatted(sum(line.move_id.partner_id.marketplace_cost_ids.mapped('salesman_commission'))) or '', light_green_body)  # Sales_Comm (%)
            col += 1
            worksheet.write(row, col, self.get_number_formatted(sum(line.move_id.partner_id.marketplace_cost_ids.mapped('other_commission'))) or '', light_green_body)  # Other_Comm (%)
            col += 1
            worksheet.write(row, col, self.get_number_formatted(sum(line.move_id.partner_id.marketplace_cost_ids.mapped('marketplace_cost'))) or '', light_green_body)  # Marketplace cost (%)
            col += 1
            worksheet.write(row, col, self.get_number_formatted(sum(line.move_id.partner_id.marketplace_cost_ids.mapped('other_cost'))) or '', light_green_body)  # Other cost (%)
            col += 1
            attribute_names = ['salesman_commission', 'other_commission', 'marketplace_cost', 'other_cost']
            total = sum(sum(line.move_id.partner_id.marketplace_cost_ids.mapped(attr)) for attr in attribute_names)
            worksheet.write(row, col, self.get_number_formatted(total) or '', light_green_body)  # Total_Comm%
            col += 1
            worksheet.write(row, col, account_ids_query or '', dark_skin_body)  # Out_Shipping_Doc
            col += 1
            worksheet.write(row, col, line.tracking_number_id.name or '', dark_skin_body)  # Tracking(AWB)
            col += 1
            Wt_Kg = sum(line.tracking_number_id.mapped('invoice_line_ids').mapped('weight_qty'))
            worksheet.write(row, col, self.get_number_formatted(round(Wt_Kg, 2)) or '', dark_skin_body)  # Tracking(AWB)_Wt_Kg
            col += 1
            worksheet.write(row, col, self.get_number_formatted(total_shipping_cost) or '', dark_skin_body)  # Out_Ship_Bill_Cost
            col += 1
            Out_SHP_Per_kg = round(total_shipping_cost/Wt_Kg ,2)  if Wt_Kg else 0.0 or 0.0
            worksheet.write(row, col, self.get_number_formatted(Out_SHP_Per_kg) or '', dark_skin_body)  # SHP_Per_kg
            col += 1

            Out_Ship_Cost_Unit = (Out_SHP_Per_kg * line.product_id.weight) or 0
            worksheet.write(row, col, self.get_number_formatted(round(Out_Ship_Cost_Unit, 2)) or '', dark_skin_body)  # Out_Ship_Cost_Unit
            col += 1
            total_sales_value = line.price_subtotal - inv_disc
            worksheet.write(row, col, self.get_number_formatted(round(total_sales_value, 2)) or '', dark_green_body)  # Total_Sales_Value
            costing_all_total_sales_value += total_sales_value
            col += 1
            # total_cn_value = total_sales_value / line.discount if line.discount else 0.0
            # if line.discount != 0:
            #     total_cn_value = total_sales_value / line.discount if line.discount else 0.0
            # else:
            #     total_cn_value = 0.0
            # total_cn_value = total_sales_value / line.discount
            prd_id = 0
            if cn_id:
                prd_id = cn_id.invoice_line_ids.filtered(lambda l: l.product_id == line.product_id)
            total_cn_value = (total_sales_value / line.quantity) * (prd_id.quantity if prd_id else 0)
            worksheet.write(row, col, self.get_number_formatted(round(total_cn_value, 2)) or '', dark_green_body) # Total_CN_Value
            costing_all_total_cn_value += total_cn_value
            col += 1
            if cn_id:
                prd_id = cn_id.invoice_line_ids.filtered(lambda l: l.product_id == line.product_id)
                worksheet.write(row, col, self.get_number_formatted(line.quantity - prd_id.quantity) or '', dark_green_body)
                costing_total_net_sales_qty += (line.quantity - prd_id.quantity)
            else:
                worksheet.write(row, col, self.get_number_formatted(line.quantity) or '', dark_green_body)  # Net_Sales_Qty
                costing_total_net_sales_qty += line.quantity
            col += 1
            total_sales_value = float(total_sales_value) if total_sales_value else 0.0
            total_cn_value = float(total_cn_value) if total_cn_value else 0.0
            net_sales_qty = total_sales_value - total_cn_value
            worksheet.write(row, col, self.get_number_formatted(round(net_sales_qty, 2)) or '', dark_green_body)  # Net_Sales-Value
            costing_total_net_sales_value += net_sales_qty
            col += 1
            # if cn_id:
            #     prd_id = cn_id.invoice_line_ids.filtered(lambda l: l.product_id == line.product_id)
            #     total = line.quantity * po_no.filtered(lambda l: l.product_id == line.product_id).price_unit if po_no else 0
            #     worksheet.write(row, col, total or 0.0, dark_green_body)
            # else:

            # Comment the below line as the MAT Cost no calculating
            # Total_Mat_Cost = (line.quantity - prd_id.quantity if prd_id else 0) * Bill_Unit_Price if po_no else 0
            Total_Mat_Cost = (line.quantity - (prd_id.quantity if prd_id else 0)) * Bill_Unit_Price if po_no else 0

            worksheet.write(row, col, self.get_number_formatted(round(Total_Mat_Cost, 2)) or 0.0, dark_green_body)  # Total_Mat_Cost
            costing_Total_Mat_Cost += Total_Mat_Cost
            col += 1
            contribution_mat = net_sales_qty - Total_Mat_Cost
            worksheet.write(row, col, self.get_number_formatted(round(contribution_mat, 2)) or 0.0, dark_green_body)  # Contribution_Mat
            costing_contribution_mat += contribution_mat
            col += 1
            mat_contr_gp1 = (contribution_mat / net_sales_qty) * 100 if net_sales_qty > 0.0 else 0.0
            worksheet.write(row, col, self.get_number_formatted(round(mat_contr_gp1, 2)) or 0.0, dark_green_body)  # Mat_Contr_GP1%
            col += 1
            in_shipping_cost = In_Ship_Cost_Unit * (line.quantity - prd_id.quantity if prd_id else 0)
            worksheet.write(row, col, self.get_number_formatted(round(in_shipping_cost, 2)) or 0.0, dark_skin_body)  # In_Shipping_Cost
            costing_in_shipping_costt += in_shipping_cost
            col += 1
            lco_gp = contribution_mat - in_shipping_cost
            worksheet.write(row, col, self.get_number_formatted(round(lco_gp, 2)) or 0.0, dark_skin_body)  # LCO_GP
            costing_lco_gp += lco_gp
            col += 1
            lco_gp_percentage = (lco_gp / net_sales_qty) * 100 if net_sales_qty > 0 else 0
            worksheet.write(row, col, self.get_number_formatted(round(lco_gp_percentage, 2)) or 0.0, dark_skin_body)  # LCO_GP%
            col += 1
            total_comm = (net_sales_qty * total) / 100
            worksheet.write(row, col, self.get_number_formatted(round(total_comm, 2)) or 0.0, dark_blue_body)  # Total_Comm
            costing_total_comm += total_comm
            col += 1
            tot_out_ship_cost = Out_Ship_Cost_Unit * line.quantity
            worksheet.write(row, col, self.get_number_formatted(round(tot_out_ship_cost, 2)) or 0.0, dark_blue_body)  # Tot_Out_Ship_Cost
            costing_tot_out_ship_cost += tot_out_ship_cost
            col += 1
            final_gp = lco_gp - total_comm - tot_out_ship_cost
            worksheet.write(row, col, self.get_number_formatted(round(final_gp, 2)) or 0.0, dark_blue_body)  # Final GP
            costing_final_gp += final_gp
            col += 1
            final_gp_percentage = (final_gp / net_sales_qty) * 100 if net_sales_qty > 0 else 0
            worksheet.write(row, col, self.get_number_formatted(round(final_gp_percentage, 2)) or 0.0, dark_blue_body)  # Final GP%
            row += 1

        worksheet.merge_range(row, 0, row, 6, ' ', border_body)
        col += 1
        worksheet.write(row, 7, 'Total', header_format)
        col += 1
        worksheet.write(row, 8, ' ', header_format)
        col += 1
        worksheet.write(row, 9, self.get_number_formatted(costing_po_total_so_qty) or 0.0, header_format)
        col += 1
        worksheet.write(row, 10, ' ', header_format)
        col += 1
        worksheet.write(row, 11, ' ', header_format)
        col += 1
        worksheet.write(row, 12, ' ', header_format)
        col += 1
        worksheet.write(row, 13, self.get_number_formatted(costing_po_total_price_subtotal) or 0.0, header_format)
        col += 1
        worksheet.write(row, 14, self.get_number_formatted(costing_po_total_inv_disc) or 0.0, header_format)
        col += 1
        worksheet.write(row, 15, ' ', header_format)
        col += 1
        worksheet.write(row, 16, ' ', header_format)
        col += 1
        worksheet.write(row, 17, self.get_number_formatted(costing_total_prd_quantity) or 0.0, header_format)
        col += 1
        worksheet.write(row, 18, ' ', header_format)
        col += 1
        worksheet.write(row, 19, ' ', header_format)
        col += 1
        worksheet.write(row, 20, ' ', header_format)
        col += 1
        worksheet.write(row, 21, ' ', header_format)
        col += 1
        worksheet.write(row, 22, ' ', header_format)
        col += 1
        worksheet.write(row, 23, ' ', header_format)
        col += 1
        worksheet.write(row, 24, ' ', header_format)
        col += 1
        worksheet.write(row, 25, ' ', header_format)
        col += 1
        worksheet.write(row, 26, ' ', header_format)
        col += 1
        worksheet.write(row, 27, ' ', header_format)
        col += 1
        worksheet.write(row, 28, ' ', header_format)
        col += 1
        worksheet.write(row, 29, ' ', header_format)
        col += 1
        worksheet.write(row, 30, ' ', header_format)
        col += 1
        worksheet.write(row, 31, ' ', header_format)
        col += 1
        worksheet.write(row, 32, ' ', header_format)
        col += 1
        worksheet.write(row, 33, ' ', header_format)
        col += 1
        worksheet.write(row, 34, ' ', header_format)
        col += 1
        worksheet.write(row, 35, ' ', header_format)
        col += 1
        worksheet.write(row, 36, ' ', header_format)
        col += 1
        worksheet.write(row, 37, ' ', header_format)
        col += 1
        worksheet.write(row, 38, ' ', header_format)
        col += 1
        worksheet.write(row, 39, self.get_number_formatted(costing_all_total_sales_value) or 0.0, header_format)
        col += 1
        worksheet.write(row, 40, self.get_number_formatted(costing_all_total_cn_value) or 0.0, header_format)
        col += 1
        worksheet.write(row, 41, self.get_number_formatted(costing_total_net_sales_qty) or 0.0, header_format)
        col += 1
        worksheet.write(row, 42, self.get_number_formatted(costing_total_net_sales_value) or 0.0, header_format)
        col += 1
        worksheet.write(row, 43, self.get_number_formatted(costing_Total_Mat_Cost) or 0.0, header_format)
        col += 1
        worksheet.write(row, 44, self.get_number_formatted(costing_contribution_mat) or 0.0, header_format)
        col += 1
        costing_total_mat_contr_gp_per = (costing_contribution_mat / costing_total_net_sales_value) * 100 if costing_total_net_sales_value else 0.0
        worksheet.write(row, 45, self.get_number_formatted(costing_total_mat_contr_gp_per) or 0.0, header_format)
        col += 1
        worksheet.write(row, 46, self.get_number_formatted(costing_in_shipping_costt) or 0.0, header_format)
        col += 1
        worksheet.write(row, 47, self.get_number_formatted(costing_lco_gp) or 0.0, header_format)
        col += 1
        costing_lco_gp_per = (costing_lco_gp / costing_total_net_sales_qty) * 100 if costing_total_net_sales_qty else 0.0
        worksheet.write(row, 48, self.get_number_formatted(costing_lco_gp_per) or 0.0, header_format)
        col += 1
        worksheet.write(row, 49, self.get_number_formatted(costing_total_comm) or 0.0, header_format)
        col += 1
        worksheet.write(row, 50, self.get_number_formatted(costing_tot_out_ship_cost) or 0.0, header_format)
        col += 1
        worksheet.write(row, 51, self.get_number_formatted(costing_final_gp) or 0.0, header_format)
        col += 1
        costing_final_gp_per = (costing_final_gp / costing_total_net_sales_value) * 100 if costing_total_net_sales_value else 0.0
        worksheet.write(row, 52, self.get_number_formatted(costing_final_gp_per) or 0.0, header_format)

        worksheet.freeze_panes(0, 8)
        worksheet.hide_gridlines(option=2)
        # close file
        workbook.close()
        # Create Attachment
        attachment = self.create_attachment(file_name)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def action_all_filter_remove(self):
        self.update({
            'date_from': '',
            'date_to': '',
            'division_ids': [(6, 0, [])],
            'partner_ids': [(6, 0, [])],
            'cso_reference': '',
            'sale_ids': [(6, 0, [])],
            'invoice_ids': [(6, 0, [])],
            'salesman_ids': [(6, 0, [])],
        })
