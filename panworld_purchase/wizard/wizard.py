# -*- coding: utf-8 -*-

import io
import base64

from datetime import datetime

from odoo import fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PurchaseXlsWizard(models.TransientModel):
    _name = 'purchase.xls.wizard'
    _description = 'purchase xls wizard'

    def action_export_xls(self, order, mail_attach=False):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Purchase order")
        formats = workbook.add_format({'font_size': 7, 'align': 'center', 'border': 1})
        format1 = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'center', 'border': 1})
        format_left = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1})
        format_left_break = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1})
        format_left_break.set_text_wrap()
        format_right = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'right', 'border': 1})

        merge_format = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9})

        merge_format_left = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 9})


        text_color = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'center', 'border': 1, 'bold': True})
        text_color_left = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1, 'bold': True})
        text_color_right = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'right', 'border': 1, 'bold': True})

        purchase = self.env['purchase.order'].browse(order)

        sheet.set_column(0,0,10)
        sheet.set_column(1,1,10)
        sheet.set_column(2,2,10)
        sheet.set_column(3,3,10)
        sheet.set_column(4,4,10)
        sheet.set_column(5,5,10)
        sheet.set_column(6,6,10)
        sheet.set_column(7,7,10)
        sheet.set_column(8,8,10)
        sheet.set_column(9,9,10)


        # sheet.merge_range('A3:B3', partner.name, text_color_left)
        # record_date = datetime.strptime(fields.Datetime.to_string(purchase.date_order), DEFAULT_SERVER_DATETIME_FORMAT).date() if purchase.date_order else ''
        # date_order = 'Date: %s' % (record_date)
        # sheet.merge_range('C3:D3', date_order, format_left)
        # sheet.merge_range('A4:B4', partner.street or '', format_left)
        # sheet.merge_range('A5:B5', partner.street2 or '', format_left)
        # city = partner.city if partner.city else ''
        # state = partner.state_id.code if partner.state_id else ''
        # zipcode = partner.zip if partner.zip else ''
        # address = city + ' ' + state + ' ' + zipcode
        # sheet.merge_range('A6:B6',  address, format_left)
        # sheet.merge_range('A7:B7', partner.country_id.name, format_left)
        # # sheet.merge_range('A8:B8', warehouse.partner_id.phone, format_left)
        # account = 'Account Number: %s' % ('')
        # sheet.merge_range('A8:B8', account, format_left)

        partner = purchase.partner_id

        if purchase.partner_id.country_id.code == 'AE':
            sheet.merge_range('A1:J2', 'Purchase Order', merge_format)
            sheet.merge_range('A3:E3', partner.name, text_color_left)
            sheet.merge_range('F3:J3', 'Ship To:', text_color_left)
            # warehouse = purchase.picking_type_id.warehouse_id
            sheet.merge_range('A4:E4', partner.street or '', format_left)
            sheet.merge_range('A5:E5', partner.street2 or '', format_left)
            # address = warehouse.partner_id.city if warehouse.partner_id.city else '' + ' ' + warehouse.partner_id.state_id.code if warehouse.partner_id.state_id else '' + ' ' + warehouse.partner_id.zip or ''
            city = partner.city if partner.city else ''
            state = partner.state_id.code if partner.state_id else ''
            zipcode = partner.zip if partner.zip else ''
            address = city + ' ' + state + ' ' + zipcode
            sheet.merge_range('A6:E6', address, format_left)
            # sheet.merge_range('A7:E7', partner.name, format_left)
            # sheet.merge_range('A8:E8', partner.phone, format_left)
            sheet.merge_range('A7:E7', partner.country_id.name, format_left)
            sheet.merge_range('A8:E8', '', format_left)
            sheet.merge_range('A9:E9', 'Account Number : %s' % (
                partner.purchase_account_number or ''), format_left)
            sheet.merge_range('A10:E10', 'Publisher : %s' % (
                purchase.publisher_id.name or ''), format_left)

            shipping = purchase.shipping_location_id
            if purchase.shipping_option_id.is_via_shipper:
                shipping = purchase.carrier_id
            if not purchase.shipping_option_id.is_via_shipper:
                sheet.merge_range('F4:J4', shipping.name, format_left)
                street = shipping.street if shipping.street else ''
                street2 = shipping.street2 if shipping.street2 else ''
                sheet.merge_range('F5:J5', street, format_left)
                sheet.merge_range('F6:J6', street2, format_left)
                city = shipping.city if shipping.city else ''
                state = shipping.state_id.code if shipping.state_id else ''
                zipcode = shipping.zip if shipping.zip else ''
                address = city + ' ' + state + ' ' + zipcode
                sheet.merge_range('F7:J7', address, format_left)
                sheet.merge_range('F8:J8', shipping.country_id.name, format_left)
                sheet.merge_range('F9:J9', shipping.phone, format_left)
                sheet.merge_range('F10:J10', '', format_left)
            if purchase.shipping_option_id.is_via_shipper:
                street = shipping.street if shipping.street else ''
                sheet.merge_range('F3:J3', 'Ship To: ' + street, text_color_left)
                street1 = shipping.street1 if shipping.street1 else ''
                sheet.merge_range('F4:J4', street1, format_left)
                street2 = shipping.street2 if shipping.street2 else ''
                sheet.merge_range('F5:J5', street2, format_left)
                city = shipping.city if shipping.city else ''
                state = shipping.state_id.code if shipping.state_id else ''
                zipcode = shipping.zip if shipping.zip else ''
                address = city + ' ' + state + ' ' + zipcode
                telephone = shipping.telephone if shipping.telephone else ''
                sheet.merge_range('F6:J6', address, format_left)
                sheet.merge_range('F7:J7', shipping.country_id.name, format_left)
                sheet.merge_range('F8:J8', 'Tel: ' + telephone, format_left)
                sheet.merge_range('F9:J9', '', format_left)
                sheet.merge_range('F10:J10', '', format_left)
        if purchase.partner_id.country_id.code != 'AE':
            sheet.merge_range('A1:I2', 'Purchase Order', merge_format)
            sheet.merge_range('A3:E3', partner.name, text_color_left)
            sheet.merge_range('F3:I3', 'Ship To:', text_color_left)
            sheet.merge_range('A4:E4', partner.street or '', format_left)
            sheet.merge_range('A5:E5', partner.street2 or '', format_left)
            city = partner.city if partner.city else ''
            state = partner.state_id.code if partner.state_id else ''
            zipcode = partner.zip if partner.zip else ''
            address = city + ' ' + state + ' ' + zipcode
            # address = shipping.partner_id.city if shipping.partner_id.city else '' + ' ' + shipping.partner_id.state_id.code if shipping.partner_id.state_id else '' + ' ' + shipping.partner_id.zip or ''
            sheet.merge_range('A6:E6', address, format_left)
            sheet.merge_range('A7:E7', partner.country_id.name, format_left)
            sheet.merge_range('A8:E8', '', format_left)
            sheet.merge_range('A9:E9', 'Account Number : %s' % (
                partner.purchase_account_number or ''), format_left)
            sheet.merge_range('A10:E10', 'Publisher : %s' % (
                purchase.publisher_id.name or ''), format_left)

            shipping = purchase.picking_type_id.warehouse_id
            shipping = purchase.shipping_location_id
            if purchase.shipping_option_id.is_via_shipper:
                shipping = purchase.carrier_id
            if not purchase.shipping_option_id.is_via_shipper:
                sheet.merge_range('F4:I4', shipping.name, format_left)
                street = shipping.street if shipping.street else ''
                street2 = shipping.street2 if shipping.street2 else ''
                sheet.merge_range('F5:I5', street, format_left)
                sheet.merge_range('F6:I6', street2, format_left)
                city = shipping.city if shipping.city else ''
                state = shipping.state_id.code if shipping.state_id else ''
                zipcode = shipping.zip if shipping.zip else ''
                address = city + ' ' + state + ' ' + zipcode
                sheet.merge_range('F7:I7', address, format_left)
                sheet.merge_range('F8:I8', shipping.country_id.name, format_left)
                sheet.merge_range('F9:I9', shipping.phone, format_left)
                sheet.merge_range('F10:I10', '', format_left)
            if purchase.shipping_option_id.is_via_shipper:
                street = shipping.street if shipping.street else ''
                sheet.merge_range('F3:I3', 'Ship To: ' + street, text_color_left)
                street1 = shipping.street1 if shipping.street1 else ''
                sheet.merge_range('F4:I4', street1, format_left)
                street2 = shipping.street2 if shipping.street2 else ''
                sheet.merge_range('F5:I5', street2, format_left)
                city = shipping.city if shipping.city else ''
                state = shipping.state_id.code if shipping.state_id else ''
                zipcode = shipping.zip if shipping.zip else ''
                address = city + ' ' + state + ' ' + zipcode
                telephone = shipping.telephone if shipping.telephone else ''
                sheet.merge_range('F6:I6', address, format_left)
                sheet.merge_range('F7:I7', shipping.country_id.name, format_left)
                sheet.merge_range('F8:I8', 'Tel: ' + telephone, format_left)
                sheet.merge_range('F9:I9', '', format_left)
                sheet.merge_range('F10:I10', '', format_left)
        date_order = fields.Date.to_string(purchase.date_order.date()) if purchase.date_order else ''
        date_planned = fields.Date.to_string(purchase.date_planned.date()) if purchase.date_planned else ''

        if purchase.partner_id.country_id.code == 'AE':
            sheet.merge_range('A11:C11', 'P.O. Date:', text_color_left)
            sheet.merge_range('D11:G11', 'Payments Term:', text_color_left)
            sheet.merge_range('H11:J11', 'Delivery Date:', text_color_left)
            sheet.merge_range('A12:C12', date_order, format_left)
            sheet.merge_range('D12:G12', purchase.payment_term_id.display_name or '', format_left)
            sheet.merge_range('H12:J12', date_planned, format_left)

            sheet.merge_range('A13:C13', 'P.O. Number:', text_color_left)
            sheet.merge_range('D13:G13', 'Currency:', text_color_left)
            sheet.merge_range('H13:J13', 'Reference:', text_color_left)
            sheet.merge_range('A14:C14', purchase.name, format_left)
            sheet.merge_range('D14:G14', purchase.currency_id.name, format_left)
            sheet.merge_range('H14:J14', purchase.partner_ref or '', format_left)
        if purchase.partner_id.country_id.code != 'AE':
            sheet.merge_range('A11:C11', 'P.O. Date:', text_color_left)
            sheet.merge_range('D11:G11', 'Payments Term:', text_color_left)
            sheet.merge_range('H11:I11', 'Delivery Date:', text_color_left)
            sheet.merge_range('A12:C12', date_order, format_left)
            sheet.merge_range('D12:G12', purchase.payment_term_id.display_name or '', format_left)
            sheet.merge_range('H12:I12', date_planned, format_left)

            sheet.merge_range('A13:C13', 'P.O. Number:', text_color_left)
            sheet.merge_range('D13:G13', 'Currency:', text_color_left)
            sheet.merge_range('H13:I13', 'Reference:', text_color_left)
            sheet.merge_range('A14:C14', purchase.name, format_left)
            sheet.merge_range('D14:G14', purchase.currency_id.name, format_left)
            sheet.merge_range('H14:I14', purchase.partner_ref or '', format_left)

        r, c = 14, 0

        # Header of Product Info
        if purchase.partner_id.country_id.code == 'AE':
            sheet.write(r, 0, 'ISBN', text_color_left)
            sheet.write(r, 1, 'Title', text_color_left)
            sheet.write(r, 2, 'Qty', text_color_right)
            sheet.write(r, 3, 'List Price', text_color_right)
            sheet.write(r, 4, 'Disc. (%)', text_color_right)
            sheet.write(r, 5, 'Unit Price', text_color_right)
            sheet.write(r, 6, 'Total', text_color_right)
            sheet.write(r, 7, 'Vat', text_color_right)
            sheet.write(r, 8, 'Vat Amount', text_color_right)
            sheet.write(r, 9, 'Net Total', text_color)
        if purchase.partner_id.country_id.code != 'AE':
            sheet.write(r, 0, 'ISBN', text_color_left)
            sheet.write(r, 1, 'Title', text_color_left)
            sheet.write(r, 2, 'Qty', text_color_right)
            sheet.write(r, 3, 'List Price', text_color_right)
            sheet.write(r, 4, 'Disc. (%)', text_color_right)
            sheet.write(r, 5, 'Unit Price', text_color_right)
            sheet.write(r, 6, 'Total', text_color_right)
            sheet.write(r, 7, 'Vat Amount', text_color_right)
            sheet.write(r, 8, 'Net Total', text_color_right)

        r += 1
        total_product_count = 0
        subtotal_sum = 0
        total_sum = 0
        po_line_dict = purchase.get_merge_duplicate_lines()
        for line in po_line_dict.values():
            c = 0
            price_total = 0
            if line.get('price_subtotal') != 0:
                price_total = line.get('price_subtotal') + line.get('vat_amount')
            else:
                price_total = line.get('price_subtotal')
            if purchase.partner_id.country_id.code == 'AE':
                sheet.write(r, c, line.get('product_id').default_code, format_left)
                c += 1
                sheet.write(r, c, line.get('product_id').name, format_left_break)
                c += 1
                sheet.write(r, c, str(line.get('product_qty')) + ' ' + str(
                    line.get('product_uom_id')), format_right)
                total_product_count = total_product_count + line.get('product_qty')
                c += 1
                sheet.write(r, c, line.get('po_list_price'), format_right)
                c += 1
                sheet.write(r, c, line.get('po_discount'), format_right)
                c += 1
                sheet.write(r, c, line.get('po_price'), format_right)
                c += 1
                sheet.write(r, c, line.get('price_subtotal'), format_right)
                subtotal_sum = subtotal_sum + line.get('price_subtotal')
                c += 1
                sheet.write(r, c, line.get('taxes_id'), format_right)
                c += 1
                sheet.write(r, c, line.get('vat_amount'), format_right)
                c += 1
                sheet.write(r, c, price_total, format_right)
                total_sum = total_sum + price_total
                c += 1
            if purchase.partner_id.country_id.code != 'AE':
                sheet.write(r, c, line.get('product_id').default_code, format_left)
                c += 1
                sheet.write(r, c, line.get('product_id').name, format_left_break)
                c += 1
                sheet.write(r, c, str(line.get('product_qty')) + ' ' + str(
                    line.get('product_uom_id')), format_right)
                total_product_count = total_product_count + line.get('product_qty')
                c += 1
                sheet.write(r, c, line.get('po_list_price'), format_right)
                c += 1
                sheet.write(r, c, line.get('po_discount'), format_right)
                c += 1
                sheet.write(r, c, line.get('po_price'), format_right)
                c += 1
                sheet.write(r, c, line.get('price_subtotal'), format_right)
                subtotal_sum = subtotal_sum + line.get('price_subtotal')
                c += 1
                sheet.write(r, c, line.get('vat_amount'), format_right)
                c += 1
                sheet.write(r, c, price_total, format_right)
                total_sum = total_sum + price_total
                c += 1
            r += 1

        if purchase.partner_id.country_id.code == 'AE':
            sheet.write(r, 2, str(total_product_count) + ' ' + str(line.get('product_uom_id')), format_right)
            sheet.write(r, 8, 'Sub Total', text_color_right)
            sheet.write(r, 9, subtotal_sum, text_color_right)
            r += 1
            sheet.write(r, 8, 'Taxes', text_color_right)
            sheet.write(r, 9, purchase.amount_tax, text_color_right)
            r += 1
            sheet.write(r, 8, 'Total', text_color_right)
            sheet.write(r, 9, total_sum, text_color_right)
            r += 3
        if purchase.partner_id.country_id.code != 'AE':
            sheet.write(r, 2, str(total_product_count) + ' ' + str(line.get('product_uom_id')), format_right)
            sheet.write(r, 7, 'Sub Total', text_color_right)
            sheet.write(r, 8, subtotal_sum, text_color_right)
            r += 1
            sheet.write(r, 7, 'Taxes', text_color_right)
            sheet.write(r, 8, purchase.amount_tax, text_color_right)
            r += 1
            sheet.write(r, 7, 'Total', text_color_right)
            sheet.write(r, 8, total_sum, text_color_right)
            r += 3

        footer = str(purchase.company_id.phone) + ' | ' + str(purchase.company_id.email) + ' | ' + str(purchase.company_id.website) + ' | VAT NO: ' + str(purchase.company_id.partner_id.vat)

        if purchase.partner_id.country_id.code == 'AE':
            sheet.merge_range('A%s:J%s' % (str(r), str(r)), footer, merge_format)
        if purchase.partner_id.country_id.code != 'AE':
            sheet.merge_range('A%s:I%s' % (str(r), str(r)), footer, merge_format)

        workbook.close()
        output.seek(0)
        data = base64.b64encode(output.getvalue())
        output.close()

        attch_obj = self.env['ir.attachment']
        attach_ids = attch_obj.search([
            ('res_model', '=', 'purchase.xls.wizard')])
        if attach_ids:
            try:
                attach_ids.unlink()
            except:
                pass

        res_id = None
        res_model = None
        doc_id = None
        if self.env.context.get('params') and self.env.context['params'].get('id'):
            res_id = self.env.context['params']['id']
            res_model = self.env.context['params']['model']

        if mail_attach:
            doc_ids = attch_obj.search(
                [('description', '=', 'po_xlsx'), ('res_model', '=', 'purchase.order'), ('res_id', '=', res_id)])
            if doc_ids and len(doc_ids) == 1:
                return doc_ids
            else:
                doc_id = attch_obj.create({
                    'name': '%s.xls' % ('Purchase Order'),
                    'datas': data,
                    'res_model': res_model if res_model else 'purchase.xls.wizard',
                    'res_id': res_id if res_id else self.id,
                    'description': 'po_xlsx',

                })
            return doc_id if doc_id else doc_ids
        else:
            doc_id = attch_obj.create({
                'name': '%s.xlsx' % ('Purchase Order'),
                'datas': data,
                'res_model': 'purchase.xls.wizard'
            })

        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/%s?download=true' % (doc_id.id),
            'target': 'current',
            'tag': 'close',
        }

    # RFQ xlsx report
    def action_rfq_export_xls(self, order, mail_attach=False):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Request for Quotation")
        formats = workbook.add_format({'font_size': 7, 'align': 'left', 'border': 1})
        format1 = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'center', 'border': 1})
        format_left = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1})
        format_left_break = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1})
        format_left_break.set_text_wrap()
        format_right = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'right', 'border': 1})

        merge_format = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9})

        merge_format_left = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 9})


        text_color = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'center', 'border': 1, 'bold': True})
        text_color_left = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1, 'bold': True})
        text_color_right = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'right', 'border': 1, 'bold': True})


        purchase = self.env['purchase.order'].browse(order)

        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 10)

        sheet.merge_range('A1:C2', 'Inquiry', merge_format)
        partner = purchase.partner_id
        sheet.write(2, 0, partner.name, text_color_left)
        date_order = fields.Datetime.to_string(purchase.date_order) if purchase.date_order else ''
        date_order = 'Date: %s' % (date_order)
        sheet.merge_range('B3:C3', date_order, format_left)
        sheet.write(3, 0, partner.street or '', format_left)
        sheet.write(4, 0, partner.street2 or '', format_left)
        city = partner.city if partner.city else ''
        state = partner.state_id.code if partner.state_id else ''
        zipcode = partner.zip if partner.zip else ''
        address = city + ' ' + state + ' ' + zipcode
        sheet.write(5, 0, address, format_left)
        sheet.write(6, 0, partner.country_id.name, format_left)
        # sheet.merge_range('A8:B8', warehouse.partner_id.phone, format_left)
        sheet.write(7, 0, 'Account Number : %s' % (
            partner.purchase_account_number or ''), format_left)
        sheet.write(8, 0, 'Publisher : %s' % (
            purchase.publisher_id.name or ''), format_left)

        doc_name = 'Doc Number: %s' % (purchase.name)
        sheet.merge_range('B4:C4', doc_name, format_left)
        reference = 'Reference: %s' % (purchase.partner_ref or '')
        sheet.merge_range('B5:C5', reference, format_left)
        # partner = purchase.shipping_location_id
        # address = partner.street + ' ' + partner.street2 if partner.street2 else ''
        # address = partner.city if partner.city else '' + ' ' + partner.state_id.code if partner.state_id else '' + ' ' + partner.zip if partner.zip else ''
        sheet.merge_range('B6:C6', '', format_left)
        sheet.merge_range('B7:C7', '', format_left)
        sheet.merge_range('B8:C8', '', format_left)
        sheet.merge_range('B9:C9', '', format_left)


        date_order = fields.Datetime.to_string(purchase.date_order) if purchase.date_order else ''
        date_planned = fields.Datetime.to_string(purchase.date_planned) if purchase.date_planned else ''
        r, c = 9, 0

        # Header of Product Info
        sheet.write(r, 0, 'ISBN', text_color_left)
        sheet.write(r, 1, 'Title', text_color_left)
        sheet.write(r, 2, 'Qty', text_color_right)

        r += 1
        total_product_count = 0
        po_line_dict = purchase.get_merge_duplicate_lines()
        for line in po_line_dict.values():
            c = 0
            sheet.write(r, c, line.get('product_id').default_code, format_left)
            c += 1
            sheet.write(r, c, line.get('product_id').name, format_left_break)
            c += 1
            sheet.write(r, c, str(line.get('product_qty')) + ' ' + str(
                line.get('product_uom_id')), format_right)
            total_product_count = total_product_count + line.get('product_qty')
            r += 1
        r += 1
        sheet.write(r, c, str(total_product_count) + ' ' + str(line.get('product_uom_id')), format_right)
        r += 3

        footer = str(purchase.company_id.phone) + ' | ' + str(purchase.company_id.email) + ' | ' + str(purchase.company_id.website) + ' | VAT NO: ' + str(purchase.company_id.partner_id.vat)

        sheet.merge_range('A%s:C%s' % (str(r), str(r)), footer, merge_format)

        workbook.close()
        output.seek(0)
        data = base64.b64encode(output.getvalue())
        output.close()

        attch_obj = self.env['ir.attachment']
        attach_ids = attch_obj.search([
            ('res_model', '=', 'purchase.xls.wizard')])
        if attach_ids:
            try:
                attach_ids.unlink()
            except:
                pass

        res_id = None
        res_model = None
        doc_id = None
        if self.env.context.get('params') and self.env.context['params'].get('id'):
            res_id = self.env.context['params']['id']
            res_model = self.env.context['params']['model']

        if mail_attach:
            doc_ids = attch_obj.search(
                [('description', '=', 'purchase_xlsx'), ('res_model', '=', 'purchase.order'), ('res_id', '=', res_id)])
            if doc_ids and len(doc_ids) == 1:
                return doc_ids
            else:
                doc_id = attch_obj.create({
                    'name': '%s.xls' % ('Request for Quotation'),
                    'datas': data,
                    'res_model': res_model if res_model else 'purchase.xls.wizard',
                    'res_id': res_id if res_id else self.id,
                    'description': 'purchase_xlsx',

                })
            return doc_id if doc_id else doc_ids
        else:
            doc_id = attch_obj.create({
                'name': '%s.xlsx' % ('Request for Quotation'),
                'datas': data,
                'res_model': 'purchase.xls.wizard'
            })
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/%s?download=true' % (doc_id.id),
            'target': 'current',
            'tag': 'close',
        }
