# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import io
import base64
from odoo import fields, models, _

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class saleXlsWizard(models.TransientModel):
    _name = 'sale.xls.wizard'
    _description = 'sale xls wizard'

    def index_to_alphabet(self,index):
        # Assuming the index starts from 1, not 0
        if 1 <= index <= 26:
            return chr(ord('A') + index - 1)

    def action_export_xls(self, order, mail_attach=False):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Sale order")
        formats = workbook.add_format({'font_size': 7, 'align': 'center', 'border': 1})
        format1 = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'center', 'border': 1})
        format_left = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1})
        format_left_break = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1})
        format_left_break.set_text_wrap()
        format_right = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'right', 'border': 1})
        format_right_zero = workbook.add_format({'num_format': '#,##0', 'font_size': 7, 'align': 'right', 'border': 1})

        merge_format = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9})

        merge_format_left = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 9})

        merge_format_amount = workbook.add_format({
            'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 7})


        text_color = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'center', 'border': 1, 'bold': True})
        text_color_left = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'left', 'border': 1, 'bold': True})
        text_color_right = workbook.add_format({'num_format': '#,##0.00', 'font_size': 7, 'align': 'right', 'border': 1, 'bold': True})

        sale = self.env['sale.order'].browse(order)

        sheet.set_column(0,0,10)
        sheet.set_column(1,1,13)
        sheet.set_column(2,2,10)
        sheet.set_column(3,3,10)
        sheet.set_column(4,4,10)
        sheet.set_column(5,5,10)
        sheet.set_column(6,6,10)
        sheet.set_column(7,7,10)
        sheet.set_column(8,8,10)
        sheet.set_column(9,9,10)
        sheet.set_column(10,10,10)


        display_discount = any(l.discount for l in sale.order_line)
        sale_state = 'Quotation # %s' % (sale.name)
        extra_fields = 10
        if display_discount:
            extra_fields += 2
        if sale.partner_id.vat == '100276002100003':
            if any(line.crn for line in sale.order_line):
                extra_fields += 1
            if any(line.course_id for line in sale.order_line):
                extra_fields += 1

        # if any(line.product_template_id.uk_wholesaler_id.name for line in sale.order_line):
        if any(line.uk_wholesaler_id.name for line in sale.order_line):
            extra_fields += 1
        if any(line.product_template_id.subject.name for line in sale.order_line):
            extra_fields += 1
        if any(line.product_template_id.non_uk_wholesaler_id.name for line in sale.order_line):
            extra_fields += 1
        if any(line.product_template_id.subtitle.name for line in sale.order_line):
            extra_fields += 1

        if display_discount:
            sheet.merge_range('A1:%s2'%(self.index_to_alphabet(extra_fields)), sale_state, merge_format)
            if sale.partner_id.vat == '100276002100003':
                sheet.merge_range('A1:%s2'%(self.index_to_alphabet(extra_fields)), sale_state, merge_format)
        else:
            sheet.merge_range('A1:%s2'%(self.index_to_alphabet(extra_fields)), sale_state, merge_format)
            if sale.partner_id.vat == '100276002100003':
                sheet.merge_range('A1:%s2'%(self.index_to_alphabet(extra_fields)), sale_state, merge_format)
        partner = sale.partner_id
        sheet.merge_range('A3:D3', partner.name, text_color_left)
        sheet.merge_range('A4:D4', partner.street or '', format_left)
        sheet.merge_range('A5:D5', partner.street2 or '', format_left)
        city = partner.city if partner.city else ''
        state = partner.state_id.code if partner.state_id else ''
        zipcode = partner.zip if partner.zip else ''
        address = city + ' ' + state + ' ' + zipcode
        sheet.merge_range('A6:D6', address, format_left)
        sheet.merge_range('A7:D7', partner.country_id.name, format_left)
        sheet.merge_range('A8:D8', partner.vat or '', format_left)
        sheet.merge_range('A9:D9', '', format_left)

        shipping = sale.partner_shipping_id
        sheet.merge_range('E3:G3', 'Shipping address:', text_color_left)
        sheet.merge_range('E4:G4', shipping.name, text_color_left)
        sheet.merge_range('E5:G5', shipping.vat or '', text_color_left)
        sheet.merge_range('E6:G6', '', format_left)
        sheet.merge_range('E7:G7', '', format_left)
        sheet.merge_range('E8:G8', '', format_left)
        sheet.merge_range('E9:G9', '', format_left)

        if display_discount:
            date_order = fields.Date.from_string(sale.date_order) if sale.date_order else ''
            date_order = 'Date: %s' % (date_order)
            sheet.merge_range('H3:%s3'%(self.index_to_alphabet(extra_fields)), date_order, text_color_left)

            doc_number = 'Doc Number: %s' % (sale.name or '')
            sheet.merge_range('H4:%s4'%(self.index_to_alphabet(extra_fields)), doc_number, text_color_left)

            ref = 'Reference: %s' % (sale.client_order_ref or '')
            sheet.merge_range('H5:%s5'%(self.index_to_alphabet(extra_fields)), ref, text_color_left)

            payment_term_id = sale.payment_term_id.name if sale.payment_term_id else ''
            payment = 'Payment Terms:: %s' % (payment_term_id)
            sheet.merge_range('H6:%s6'%(self.index_to_alphabet(extra_fields)), payment, text_color_left)

            currency = sale.currency_id.name if sale.currency_id else ''
            currency = 'Currency: %s' % (currency)
            sheet.merge_range('H7:%s7'%(self.index_to_alphabet(extra_fields)), currency, text_color_left)

            sheet.merge_range('H8:%s8'%(self.index_to_alphabet(extra_fields)), '', format_left)
            sheet.merge_range('H9:%s9'%(self.index_to_alphabet(extra_fields)), '', format_left)
            sheet.merge_range('H10:%s10'%(self.index_to_alphabet(extra_fields)), '', format_left)
            if sale.partner_id.vat == '100276002100003':
                sheet.merge_range('H3:%s3'%(self.index_to_alphabet(extra_fields)), date_order, text_color_left)
                sheet.merge_range('H4:%s4'%(self.index_to_alphabet(extra_fields)), doc_number, text_color_left)
                sheet.merge_range('H5:%s5'%(self.index_to_alphabet(extra_fields)), ref, text_color_left)
                sheet.merge_range('H6:%s6'%(self.index_to_alphabet(extra_fields)), payment, text_color_left)
                sheet.merge_range('H7:%s7'%(self.index_to_alphabet(extra_fields)), currency, text_color_left)
                sheet.merge_range('H8:%s8'%(self.index_to_alphabet(extra_fields)), '', format_left)
                sheet.merge_range('H9:%s9'%(self.index_to_alphabet(extra_fields)), '', format_left)
                sheet.merge_range('H10:%s10'%(self.index_to_alphabet(extra_fields)), '', format_left)

        else:
            date_order = fields.Date.from_string(sale.date_order) if sale.date_order else ''
            date_order = 'Date: %s' % (date_order)
            sheet.merge_range('H3:%s3'%(self.index_to_alphabet(extra_fields)), date_order, text_color_left)

            doc_number = 'Doc Number: %s' % (sale.name or '')
            sheet.merge_range('H4:%s4'%(self.index_to_alphabet(extra_fields)), doc_number, text_color_left)

            ref = 'Reference: %s' % (sale.client_order_ref or '')
            sheet.merge_range('H5:%s5'%(self.index_to_alphabet(extra_fields)), ref, text_color_left)

            payment_term_id = sale.payment_term_id.name if sale.payment_term_id else ''
            payment = 'Payment Terms:: %s' % (payment_term_id)
            sheet.merge_range('H6:%s6'%(self.index_to_alphabet(extra_fields)), payment, text_color_left)

            currency = sale.currency_id.name if sale.currency_id else ''
            currency = 'Currency: %s' % (currency)
            sheet.merge_range('H7:%s7'%(self.index_to_alphabet(extra_fields)), currency, text_color_left)

            sheet.merge_range('H8:%s8'%(self.index_to_alphabet(extra_fields)), '', format_left)
            sheet.merge_range('H9:%s9'%(self.index_to_alphabet(extra_fields)), '', format_left)
            sheet.merge_range('H10:%s10'%(self.index_to_alphabet(extra_fields)), '', format_left)
            if sale.partner_id.vat == '100276002100003':
                sheet.merge_range('H3:%s3'%(self.index_to_alphabet(extra_fields)), date_order, text_color_left)
                sheet.merge_range('H4:%s4'%(self.index_to_alphabet(extra_fields)), doc_number, text_color_left)
                sheet.merge_range('H5:%s5'%(self.index_to_alphabet(extra_fields)), ref, text_color_left)
                sheet.merge_range('H6:%s6'%(self.index_to_alphabet(extra_fields)), payment, text_color_left)
                sheet.merge_range('H7:%s7'%(self.index_to_alphabet(extra_fields)), currency, text_color_left)
                sheet.merge_range('H8:%s8'%(self.index_to_alphabet(extra_fields)), '', format_left)
                sheet.merge_range('H9:%s9'%(self.index_to_alphabet(extra_fields)), '', format_left)
                sheet.merge_range('H10:%s10'%(self.index_to_alphabet(extra_fields)), '', format_left)

        r, c = 10, 0

        sheet_count = 0

        # Header of Product Info
        sheet.write(r, sheet_count, 'S No.', text_color)
        sheet_count += 1
        sheet.write(r, sheet_count, 'ISBN', text_color)
        sheet_count += 1
        sheet.write(r, sheet_count, 'Product Name', text_color)

        # As per client requirement add 2 column base on customer vat number
        if sale.partner_id.vat == '100276002100003' and any(line.course_id for line in sale.order_line):
            sheet_count += 1
            sheet.write(r, sheet_count, 'Course ID', text_color_right)

        # if any(line.product_template_id.uk_wholesaler_id.name for line in sale.order_line):
        if any(line.uk_wholesaler_id.name for line in sale.order_line):
            sheet_count += 1
            sheet.write(r, sheet_count, 'Grade', text_color_right)
        if any(line.product_template_id.subject.name for line in sale.order_line):
            sheet_count += 1
            sheet.write(r, sheet_count, 'Subject', text_color_right)
        if any(line.product_template_id.non_uk_wholesaler_id.name for line in sale.order_line):
            sheet_count += 1
            sheet.write(r, sheet_count, 'Classification', text_color_right)
        if any(line.product_template_id.subtitle.name for line in sale.order_line):
            sheet_count += 1
            sheet.write(r, sheet_count, 'Format', text_color_right)

        if sale.partner_id.vat == '100276002100003' and any(line.crn for line in sale.order_line):
            sheet_count += 1
            sheet.write(r, sheet_count, 'CRN', text_color_right)
        sheet_count += 1
        sheet.write(r, sheet_count, 'Quotation QTY', text_color_right)
        sheet_count += 1
        if display_discount:
            sheet.write(r, sheet_count, 'List Price', text_color_right)
            sheet_count += 1
            sheet.write(r, sheet_count, 'Disc. (%)', text_color_right)
            sheet_count += 1
        sheet.write(r, sheet_count, 'Unit Price', text_color_right)
        sheet_count += 1
        sheet.write(r, sheet_count, 'Total', text_color_right)
        sheet_count += 1
        sheet.write(r, sheet_count, 'Vat', text_color_right)
        sheet_count += 1
        sheet.write(r, sheet_count, 'Vat Amount', text_color_right)
        sheet_count += 1
        sheet.write(r, sheet_count, 'Net Total', text_color_right)

        sheet_count += 1
        sheet.write(r, sheet_count, 'Remark', text_color_right)
        r += 1


        count = 0
        total_product_count = 0
        subtotal_sum = 0
        total_sum = 0
        for line in sale.order_line:
            c = 0
            count += 1
            sheet.write(r, c, count, formats)
            c += 1
            sheet.write(r, c, line.product_id.default_code or '', format_left_break)
            c += 1
            sheet.write(r, c, line.product_id.name or '', format_left_break)

            if sale.partner_id.vat == '100276002100003' and any(line.course_id for line in sale.order_line):
                c += 1
                sheet.write(r, c, line.course_id or '', format_left_break)

            # if any(td.product_template_id.uk_wholesaler_id.name for td in sale.order_line):
            #     c += 1
            #     sheet.write(r, c,
            #                 line.product_template_id.uk_wholesaler_id.name if line.product_template_id.uk_wholesaler_id else '',
            #                 format_right)
            if any(td.uk_wholesaler_id.name for td in sale.order_line):
                c += 1
                sheet.write(r, c,
                            line.uk_wholesaler_id.name if line.uk_wholesaler_id else '',
                            format_right)
            if any(td.product_template_id.subject.name for td in sale.order_line):
                c += 1
                sheet.write(r, c, line.product_template_id.subject.name if line.product_template_id.subject else '',
                            format_right)
            if any(td.product_template_id.non_uk_wholesaler_id.name for td in sale.order_line):
                c += 1
                sheet.write(r, c,
                            line.product_template_id.non_uk_wholesaler_id.name if line.product_template_id.non_uk_wholesaler_id else '',
                            format_right)
            if any(td.product_template_id.subtitle for td in sale.order_line):
                c += 1
                sheet.write(r, c,
                            line.product_template_id.subtitle.name if line.product_template_id.subtitle else '',
                            format_right)
            if sale.partner_id.vat == '100276002100003' and any(line.crn for line in sale.order_line):
                c += 1
                sheet.write(r, c, line.crn or '', format_left_break)
            c += 1
            sheet.write(r, c, line.so_qty, format_right_zero)
            total_product_count = total_product_count + line.so_qty
            c += 1
            if display_discount:
                sheet.write(r, c, line.price_unit, format_right)
                c += 1
                sheet.write(r, c, line.discount, format_right)
                c += 1
            sheet.write(r, c, line.list_price, format_right)
            c += 1
            price_subtotal = line.so_qty * line.list_price
            sheet.write(r, c, price_subtotal, format_right)
            subtotal_sum = subtotal_sum + price_subtotal
            c += 1
            # tax = ', '.join(map(lambda x: (str(int(x.amount)) + '%'), line.tax_id))
            sheet.write(r, c, (', '.join(map(lambda x: str(x.amount) + '%', line.tax_ids))), format_right_zero)
            c += 1
            vat = line.price_total - line.price_subtotal
            sheet.write(r, c, vat, format_right)
            c += 1
            total = vat + price_subtotal
            sheet.write(r, c, total, format_right)
            total_sum = total_sum + total


            c += 1
            sheet.write(r, c, line.remarks or '', format_right)
            r += 1

        if display_discount:
            r += 1
            price_reduce = sum(((l.product_uom_qty * l.price_unit) * (l.discount/100)) for l in sale.order_line)
            sheet.merge_range(r,sheet_count - 2,r, sheet_count - 1, 'Discount', text_color_right)
            discount = '%s %s' % (price_reduce, sale.currency_id.name)
            sheet.write(r, sheet_count,  discount, text_color_right)

        r += 1
        sheet.merge_range(r,sheet_count - 2,r, sheet_count - 1, 'Untaxed Amount', text_color_right)
        amount = '%s %s' % (subtotal_sum, sale.currency_id.name)
        sheet.write(r, sheet_count,  amount, text_color_right)

        r += 1
        tax = ', '.join(map(lambda x: str(x.name), line.tax_ids))
        sheet.merge_range(r,sheet_count - 2,r, sheet_count - 1, tax, text_color_right)
        taxes = '%s %s' % (sale.amount_tax, sale.currency_id.name)
        sheet.write(r, sheet_count,  taxes, text_color_right)

        r += 1
        sheet.merge_range(r,sheet_count - 2,r, sheet_count - 1, 'Total', text_color_right)
        total = '%s %s' % (total_sum, sale.currency_id.name)
        sheet.write(r, sheet_count,  total, text_color_right)


        r += 1
        product_uom_qty = str(int(sum(l.product_uom_qty for l in sale.order_line)))
        # sheet.write(r, sheet_count - 1, 'Total Units', text_color_right)
        sheet.merge_range(r,sheet_count - 2,r, sheet_count - 1, 'Total Units', text_color_right)
        sheet.write(r, sheet_count,  product_uom_qty, text_color_right)

        r += 2
        amount_in_word = 'Amount In Words : %s' % (sale.currency_id.amount_to_text(sale.amount_total))
        if display_discount:
            sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r)), amount_in_word, merge_format_amount)
            if sale.partner_id.vat == '100276002100003':
                sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r)), amount_in_word, merge_format_amount)
        else:
            sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r)), amount_in_word, merge_format_amount)
            if sale.partner_id.vat == '100276002100003':
                sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r)), amount_in_word, merge_format_amount)

        r += 2
        # note = html2text.html2text(sale.note)
        # if display_discount:
        #     sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r + 8)), note, merge_format_amount)
        #     if sale.partner_id.vat == '100276002100003':
        #         sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r + 8)), note, merge_format_amount)
        # else:
        #     sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r + 8)), note, merge_format_amount)
        #     if sale.partner_id.vat == '100276002100003':
        #         sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)) ,str(r + 8)), note, merge_format_amount)

        # r += 10
        footer = str(sale.company_id.phone) + ' | ' + str(sale.company_id.email) + ' | ' + str(sale.company_id.website) + ' | VAT NO: ' + str(sale.company_id.partner_id.vat)
        if display_discount:
            sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)) ,str(r)), footer, merge_format)
            if sale.partner_id.vat == '100276002100003':
                sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r)), footer, merge_format)
        else:
            sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)), str(r)), footer, merge_format)
            if sale.partner_id.vat == '100276002100003':
                sheet.merge_range('A%s:%s%s' % (str(r),(self.index_to_alphabet(extra_fields)) ,str(r)), footer, merge_format)

        workbook.close()
        output.seek(0)
        data = base64.b64encode(output.getvalue())
        output.close()

        attch_obj = self.env['ir.attachment']
        attach_ids = attch_obj.search([
            ('res_model', '=', 'sale.xls.wizard')])
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
                [('description', '=', 'sale_xlsx'), ('res_model', '=', 'sale.order'), ('res_id', '=', res_id)])
            if doc_ids and len(doc_ids) == 1:
                return doc_ids
            else:
                doc_id = attch_obj.create({
                    'name': '%s.xls' % ('Sale Order'),
                    'datas': data,
                    'res_model': res_model if res_model else 'sale.xls.wizard',
                    'res_id': res_id if res_id else self.id,
                    'description': 'sale_xlsx',

                })
            return doc_id if doc_id else doc_ids
        else:
            doc_id = attch_obj.create({
                'name': '%s.xls' % ('Sale Order'),
                'datas': data,
                'res_model': res_model if res_model else 'sale.xls.wizard',
                'res_id': res_id if res_id else self.id,  # self._context.get('active_id') -- used for active_id

            })

        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/%s?download=true' % (doc_id.id if doc_id else None),
            'target': 'current',
            'tag': 'close',
        }
