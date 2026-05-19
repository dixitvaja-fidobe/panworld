# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from  datetime import datetime

class ResHistory(models.Model):
    _name = "res.history"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Records History"
    _rec_name = 'name'



    def domain_contact_data(self):
        domain = [("company_id", "in", self.env.companies.ids)]
        if self.env.context and self.env.context.get('params') and self.env.context.get('params').get(
                'model') == 'res.history' and self.env.context.get('params').get('id'):
            history_id = self.env[self.env.context.get('params').get('model')].sudo().browse(
                self.env.context.get('params').get('id'))
            if history_id and history_id.contact_ids:
                domain += [('partner_id', 'in', history_id.contact_ids.ids)]
        return domain

    def domain_invoice_ids(self):
        domain = [('move_type', '=', 'out_invoice'), ("company_id", "in", self.env.companies.ids)]
        if self.env.context and self.env.context.get('params') and self.env.context.get('params').get(
                'model') == 'res.history' and self.env.context.get('params').get('id'):
            history_id = self.env[self.env.context.get('params').get('model')].sudo().browse(
                self.env.context.get('params').get('id'))
            print ("historyyyyyyyy",history_id)
            if history_id and history_id.contact_ids:
                domain += [('partner_id', 'in', history_id.contact_ids.ids)]
        return domain

    def domain_credit_note_ids(self):
        domain = [('move_type', '=', 'out_refund'), ("company_id", "in", self.env.companies.ids)]
        if self.env.context and self.env.context.get('params') and self.env.context.get('params').get(
                'model') == 'res.history' and self.env.context.get('params').get('id'):
            history_id = self.env[self.env.context.get('params').get('model')].sudo().browse(
                self.env.context.get('params').get('id'))
            if history_id and history_id.contact_ids:
                domain += [('partner_id', 'in', history_id.contact_ids.ids)]
        return domain

    def domain_bill_ids(self):
        domain = [('move_type', '=', 'in_invoice'), ("company_id", "in", self.env.companies.ids)]
        if self.env.context and self.env.context.get('params') and self.env.context.get('params').get(
                'model') == 'res.history' and self.env.context.get('params').get('id'):
            history_id = self.env[self.env.context.get('params').get('model')].sudo().browse(
                self.env.context.get('params').get('id'))
            if history_id and history_id.contact_ids:
                domain += [('partner_id', 'in', history_id.contact_ids.ids)]
        return domain


    def domain_delivery_note_ids(self):
        domain = [('picking_type_id.code', '=', 'outgoing'), ("company_id", "in", self.env.companies.ids), ("name", "=like", 'DN%')]
        if self.env.context and self.env.context.get('params') and self.env.context.get('params').get(
                'model') == 'res.history' and self.env.context.get('params').get('id'):
            history_id = self.env[self.env.context.get('params').get('model')].sudo().browse(
                self.env.context.get('params').get('id'))
            if history_id and history_id.contact_ids:
                domain += [('partner_id', 'in', history_id.contact_ids.ids)]
        return domain

    def domain_vendor_credit_ids(self):
        domain = [('move_type', '=', 'in_refund'), ("company_id", "in", self.env.companies.ids)]
        if self.env.context and self.env.context.get('params') and self.env.context.get('params').get(
                'model') == 'res.history' and self.env.context.get('params').get('id'):
            history_id = self.env[self.env.context.get('params').get('model')].sudo().browse(
                self.env.context.get('params').get('id'))
            if history_id and history_id.contact_ids:
                domain += [('partner_id', 'in', history_id.contact_ids.ids)]
        return domain

    def domain_grn_ids(self):
        domain = [('picking_type_id.code', '=', 'incoming'), ("company_id", "in", self.env.companies.ids), ("name", "=like", 'GRN%')]
        if self.env.context and self.env.context.get('params') and self.env.context.get('params').get(
                'model') == 'res.history' and self.env.context.get('params').get('id'):
            history_id = self.env[self.env.context.get('params').get('model')].sudo().browse(
                self.env.context.get('params').get('id'))
            if history_id and history_id.contact_ids:
                domain += [('partner_id', 'in', history_id.contact_ids.ids)]
        return domain




    name = fields.Char()
    product_id = fields.Many2many('product.product', relation='product_history_rel',string='Product')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    contact_ids = fields.Many2many('res.partner', relation='contact_history_rel', string='Contact Name')
    transaction_type = fields.Selection(selection=[
        ('purchase_order', 'Purchase Order'),
        ('sale_order', 'Sales Order'),
        ('invoices', 'Invoices'),
        ('bills', 'Bills'),
        ('credit_note', 'Credit Note'),
        ('vendor_credit', 'Vendor Credit'),
        ('grn', 'GRN'),
        ('delivery_note', 'Delivery Note'),
        ('inventory_adjustment', 'Inventory Adjustment'),
    ], required=True)
    document_num = fields.Char('Doc Num')
    sale_order_ids = fields.Many2many('sale.order',relation='sale_res_history_rel',string='Doc Num',check_company=True,domain=domain_contact_data)
    invoice_ids = fields.Many2many('account.move',relation='invoice_res_history_rel' ,string='Doc Num', check_company=True,
                                      domain=domain_invoice_ids)
    purchase_order_ids = fields.Many2many('purchase.order',relation='purchase_res_history_rel',string='Doc Num',check_company=True,domain=domain_contact_data)
    credit_note_ids = fields.Many2many('account.move', relation='credit_note_res_history_rel', string='Doc Num',
                                   check_company=True,
                                   domain=domain_credit_note_ids)
    bill_ids = fields.Many2many('account.move', relation='bill_res_history_rel', string='Doc Num', check_company=True,
                                domain=domain_bill_ids)
    delivery_note_ids = fields.Many2many('stock.picking', relation='delivery_note_res_history_rel', string='Doc Num', check_company=True,
                                domain=domain_delivery_note_ids)

    vendor_credit_ids = fields.Many2many('account.move', relation='vendor_credit_res_history_rel', string='Doc Num', check_company=True,
                                domain=domain_vendor_credit_ids)

    grn_ids = fields.Many2many('stock.picking', relation='grn_res_history_rel', string='Doc Num',
                                         check_company=True,
                                         domain=domain_grn_ids)


    @api.model
    def create(self,vals):
        res = super().create(vals)
        res.name = dict(res._fields['transaction_type'].selection).get(res.transaction_type)
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'transaction_type' in vals and vals['transaction_type']:
                rec.name = dict(self._fields['transaction_type'].selection).get(rec.transaction_type)
        return res

    

    @api.constrains('date_from', 'date_to')
    def _constraint_between_start_end_date(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise AccessError(_("To Date must be grater than From Date!"))

    @api.onchange('contact_ids')
    def get_document_num_domain(self):
        for rec in self:
            domain = [('company_id', 'in', self.env.companies.ids)]
            field = ''
            if rec.transaction_type == 'sale_order':
                field = 'sale_order_ids'
                if rec.contact_ids:
                    domain += [('partner_id', 'in', rec.contact_ids.ids)]
            elif rec.transaction_type == 'invoices':
                domain += [('move_type', '=', 'out_invoice')]
                field = 'invoice_ids'
                if rec.contact_ids:
                    domain += [('partner_id', 'in', rec.contact_ids.ids)]
            elif rec.transaction_type == 'purchase_order':
                field = 'purchase_order_ids'
                if rec.contact_ids:
                    domain += [('partner_id', 'in', rec.contact_ids.ids)]
            elif rec.transaction_type == 'credit_note':
                domain += [('move_type', '=', 'out_refund')]
                field = 'credit_note_ids'
                if rec.contact_ids:
                    domain += [('partner_id', 'in', rec.contact_ids.ids)]
            elif rec.transaction_type == 'bills':
                domain += [('move_type', '=', 'in_invoice')]
                field = 'bill_ids'
                if rec.contact_ids:
                    domain += [('partner_id', 'in', rec.contact_ids.ids)]
            elif rec.transaction_type == 'delivery_note':
                domain += [('picking_type_id.code', '=', 'outgoing'),("name", "=like", 'DN%')]
                field = 'delivery_note_ids'
            elif rec.transaction_type == 'vendor_credit':
                domain += [('move_type', '=', 'in_refund')]
                field = 'vendor_credit_ids'
                if rec.contact_ids:
                    domain += [('partner_id', 'in', rec.contact_ids.ids)]
            elif rec.transaction_type == 'grn':
                domain += [('picking_type_id.code', '=', 'incoming'),("name", "=like", 'GRN%')]
                field = 'grn_ids'
                if rec.contact_ids:
                    domain += [('partner_id', 'in', rec.contact_ids.ids)]
            if field:
                return {'domain': {field: domain}}

    def _sql_sale_order(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,date_order,order_reference,sale_order_id,partner_id,customer_sales_order,barcode,division_type_id,description,currency_id,
                    price_unit,discount,list_price,so_quantity,qty_delivered,qty_invoiced,
                    price_subtotal,company_id,state)

                select
                    {report_id} AS report_id,
                    s_order.date_order as date_order,
                    s_order.name as order_reference,
                    s_order.id as sale_order_id,
                    s_order.partner_id as partner_id,
                    s_order.customer_sales_order as customer_sales_order,
                    product.barcode as barcode,
                    s_order.division_type_id as division_type_id,
                    product_tem.name as description,
                    s_order.currency_id as currency_id,
                    s_order_line.price_unit as price_unit,
                    s_order_line.discount as discount,
                    s_order_line.list_price as list_price,
                    s_order_line.so_quantity as so_quantity,
                    s_order_line.qty_delivered as qty_delivered,
                    s_order_line.qty_invoiced as qty_invoiced,
                    s_order_line.price_subtotal as price_subtotal,
                    s_order.company_id as company_id,
                    s_order.state as state
                    from sale_order_line s_order_line
                    join sale_order s_order on s_order.id = s_order_line.order_id 
                    join product_product product on product.id = s_order_line.product_id 
                    join product_template product_tem on product_tem.id = product.product_tmpl_id
                    """

        where_clause = []
        if len(self.env.companies) > 1:
            where_clause.append(f"""s_order.company_id in {str(tuple(self.env.companies.ids))}""")
        else:
            where_clause.append(f"""s_order.company_id = {self.env.companies[0].id}""")
        if self.date_from:
            where_clause.append(f"""s_order.date_order >= '{self.date_from.strftime('%Y-%m-%d') + ' 00:00:00'}'""")
        if self.date_to:
            where_clause.append(f"""s_order.date_order <= '{self.date_to.strftime('%Y-%m-%d') + ' 23:59:59'}'""")
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(f"""s_order_line.product_id = {self.product_id[0].id}""")
            else:
                where_clause.append(f"""s_order_line.product_id in {str(tuple(self.product_id.ids))}""")
        if self.contact_ids:
            if len(self.contact_ids) == 1:
                where_clause.append(f"""s_order.partner_id = {self.contact_ids[0].id}""")
            else:
                where_clause.append(f"""s_order.partner_id in {str(tuple(self.contact_ids.ids))}""")
        if self.sale_order_ids:
            if len(self.sale_order_ids) == 1:
                where_clause.append(f"""s_order.id = {self.sale_order_ids[0].id}""")
            else:
                where_clause.append(f"""s_order.id in {str(tuple(self.sale_order_ids.ids))}""")
        if where_clause:
            query += ' where '+' and '.join(where_clause)
        self.env.cr.execute(query)

    def _sql_invoices(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,invoice_date,invoice_number,invoice_id,partner_id,delivery_note,order_reference,cso_reference,barcode,
                    description,price_unit,discount,list_price,quantity,vat_amount,
                    price_subtotal,company_id,invoice_state,currency_id)
                    
                select
                    {report_id} AS report_id,
                    invoice.invoice_date as invoice_date,
                    invoice.name as invoice_number,
                    invoice.id as invoice_id,
                    invoice.partner_id as partner_id,
                    picking.name as delivery_note,
                    s_order.name as order_reference,
                    invoice.tracking_ref as cso_reference,
                    product.barcode as barcode,
                    product_tem.name as description,
                    invoice_line.price_unit as price_unit,
                    invoice_line.discount as discount,
                    invoice_line.list_price as list_price,
                    invoice_line.quantity as quantity,
                    (invoice_line.price_total - invoice_line.price_subtotal) as vat_amount,
                    invoice_line.price_subtotal as price_subtotal,
                    invoice.company_id as company_id,
                    invoice.state as invoice_state,
                    invoice.currency_id as currency_id
                    from account_move_line invoice_line
                    join account_move invoice on invoice.id = invoice_line.move_id 
                    join product_product product on product.id = invoice_line.product_id 
                    join product_template product_tem on product_tem.id = product.product_tmpl_id 
                    left join sale_order_line_invoice_rel sale_line_invoice_line on sale_line_invoice_line.invoice_line_id = invoice_line.id
                    left join sale_order_line s_order_line on s_order_line.id = sale_line_invoice_line.order_line_id
                    left join sale_order s_order on s_order.id =  s_order_line.order_id
                    left join ( select amspr.account_move_id, string_agg(sp.name, ', ') as name from account_move_stock_picking_rel amspr 
                    left join account_move am on am.id = amspr.account_move_id
                    left join stock_picking sp on sp.id = amspr.stock_picking_id
                    group by amspr.account_move_id
                    ) picking on picking.account_move_id = invoice.id
                    """
        where_clause = []
        where_clause.append("""invoice.move_type = 'out_invoice'""")
        if len(self.env.companies) > 1:
            where_clause.append(f"""invoice.company_id in {str(tuple(self.env.companies.ids))}""")
        else:
            where_clause.append(f"""invoice.company_id = {self.env.companies[0].id}""")
        if self.date_from:
            where_clause.append(f"""invoice.invoice_date >= '{self.date_from}'""")
        if self.date_to:
            where_clause.append(f"""invoice.invoice_date <= '{self.date_to}'""")
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(f"""invoice_line.product_id = {self.product_id[0].id}""")
            else:
                where_clause.append(f"""invoice_line.product_id in {str(tuple(self.product_id.ids))}""")
        if self.contact_ids:
            if len(self.contact_ids) == 1:
                where_clause.append(f"""invoice.partner_id = {self.contact_ids[0].id}""")
            else:
                where_clause.append(f"""invoice.partner_id in {str(tuple(self.contact_ids.ids))}""")
        if self.invoice_ids:
            if len(self.invoice_ids) == 1:
                where_clause.append(f"""invoice.id = {self.invoice_ids[0].id}""")
            else:
                where_clause.append(f"""invoice.id in {str(tuple(self.invoice_ids.ids))}""")
        if where_clause:
            query += " where "+' and '.join(where_clause)
        self.env.cr.execute(query)
        
    def _sql_purchase_order(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,date_order,order_reference,purchase_order_id,partner_id,customer_name,customer_order_number,
                    customer_sales_order,barcode,description,currency_id,po_list_price,po_discount,po_price,
                    po_qty,qty_received,qty_invoiced,price_subtotal,company_id,po_state)
                select
                    {report_id} AS report_id,
                    p_order.date_order as date_order,
                    p_order.name as order_reference,
                    p_order.id as purchase_order_id,
                    p_order.partner_id as partner_id,
                    p_order_line.customer_name as customer_name,
                    p_order_line.customer_sales_order as customer_order_number,
                    p_order_line.sale_reference as customer_sales_order,
                    product.barcode as barcode,
                    product_tem.name as description,
                    p_order.currency_id as currency_id,
                    p_order_line.po_list_price as po_list_price,
                    p_order_line.po_discount as po_discount,
                    p_order_line.po_price as po_price,
                    p_order_line.po_qty as po_qty,
                    p_order_line.qty_received as qty_received,
                    p_order_line.qty_invoiced as qty_invoiced,
                    p_order_line.price_subtotal as price_subtotal,
                    p_order.company_id as company_id,
                    p_order.state as po_state
                    from purchase_order_line p_order_line
                    join purchase_order p_order on p_order.id = p_order_line.order_id 
                    join product_product product on product.id = p_order_line.product_id 
                    join product_template product_tem on product_tem.id = product.product_tmpl_id 
                    """

        where_clause = []
        if len(self.env.companies) > 1:
            where_clause.append(
                f"""p_order.company_id in {str(tuple(self.env.companies.ids))}"""
            )
        else:
            where_clause.append(
                f"""p_order.company_id = {self.env.companies[0].id}"""
            )
        if self.date_from:
            where_clause.append(
                f"""p_order.date_order >= '{self.date_from.strftime('%Y-%m-%d') + ' 00:00:00'}'"""
            )
        if self.date_to:
            where_clause.append(
                f"""p_order.date_order <= '{self.date_to.strftime('%Y-%m-%d') + ' 23:59:59'}'"""
            )
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(
                    f"""p_order_line.product_id = {self.product_id[0].id}"""
                )
            else:
                where_clause.append(
                    f"""p_order_line.product_id in {str(tuple(self.product_id.ids))}"""
                )
        if self.contact_ids:
            if len(self.contact_ids) == 1:
                where_clause.append(
                    f"""p_order.partner_id = {self.contact_ids[0].id}"""
                )
            else:
                where_clause.append(
                    f"""p_order.partner_id in {str(tuple(self.contact_ids.ids))}"""
                )
        if self.purchase_order_ids:
            if len(self.purchase_order_ids) == 1:
                where_clause.append(
                    f"""p_order.id = {self.purchase_order_ids[0].id}"""
                )
            else:
                where_clause.append(
                    f"""p_order.id in {str(tuple(self.purchase_order_ids.ids))}"""
                )
        if where_clause:
            query += " where " + " and ".join(where_clause)
        self.env.cr.execute(query)

    def _sql_credit_note(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,invoice_date,invoice_number,invoice_id,partner_id,cso_reference,sale_order_id,rma_id,barcode,
                    description,list_price,quantity,
                    price_subtotal,company_id,invoice_state,currency_id)

                select
                    {report_id} AS report_id,
                    invoice.invoice_date as invoice_date,
                    invoice.name as invoice_number,
                    invoice.id as invoice_id,
                    invoice.partner_id as partner_id,
                    invoice.tracking_ref as cso_reference,
                    rma.sale_order_id as sale_order_id,
                    rma.id as rma_id,
                    product.barcode as barcode,
                    product_tem.name as description,
                    invoice_line.list_price as list_price,
                    invoice_line.quantity as quantity,
                    invoice_line.price_subtotal as price_subtotal,
                    invoice.company_id as company_id,
                    invoice.state as invoice_state,
                    invoice.currency_id as currency_id
                    from account_move_line invoice_line
                    join account_move invoice on invoice.id = invoice_line.move_id 
                    join product_product product on product.id = invoice_line.product_id 
                    join product_template product_tem on product_tem.id = product.product_tmpl_id 
                    left join rma_ret_mer_auth rma on rma.id = invoice.rma_id 
                    """
        where_clause = []
        where_clause.append("""invoice.move_type = 'out_refund'""")
        if len(self.env.companies) > 1:
            where_clause.append(f"""invoice.company_id in {str(tuple(self.env.companies.ids))}""")
        else:
            where_clause.append(f"""invoice.company_id = {self.env.companies[0].id}""")
        if self.date_from:
            where_clause.append(f"""invoice.invoice_date >= '{self.date_from}'""")
        if self.date_to:
            where_clause.append(f"""invoice.invoice_date <= '{self.date_to}'""")
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(f"""invoice_line.product_id = {self.product_id[0].id}""")
            else:
                where_clause.append(f"""invoice_line.product_id in {str(tuple(self.product_id.ids))}""")
        if self.contact_ids:
            if len(self.contact_ids) == 1:
                where_clause.append(f"""invoice.partner_id = {self.contact_ids[0].id}""")
            else:
                where_clause.append(f"""invoice.partner_id in {str(tuple(self.contact_ids.ids))}""")
        if self.credit_note_ids:
            if len(self.credit_note_ids) == 1:
                where_clause.append(f"""invoice.id = {self.credit_note_ids[0].id}""")
            else:
                where_clause.append(f"""invoice.id in {str(tuple(self.credit_note_ids.ids))}""")
        if where_clause:
            query += " where " + ' and '.join(where_clause)
        self.env.cr.execute(query)
        
    def _sql_bills(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,invoice_date,invoice_number,invoice_id,partner_id,barcode,
                    description,currency_id,price_unit,discount,list_price,quantity,vat_amount,
                    price_subtotal,product_weight,tracking_number,company_id,invoice_state)

                select
                    {report_id} AS report_id,
                    bill.invoice_date as invoice_date,
                    bill.name as invoice_number,
                    bill.id as invoice_id,
                    bill.partner_id as partner_id,
                    product.barcode as barcode,
                    product_tem.name as description,
                    bill.currency_id as currency_id,
                    bill_line.price_unit as price_unit,
                    bill_line.discount as discount,
                    bill_line.list_price as list_price,
                    bill_line.quantity as quantity,
                    (bill_line.price_total - bill_line.price_subtotal) as vat_amount,
                    bill_line.price_subtotal as price_subtotal,
                    product.weight as product_weight,
                    bill.tracking_number_bill_id as tracking_number,
                    bill.company_id as company_id,
                    bill.state as invoice_state
                    from account_move_line bill_line
                    join account_move bill on bill.id = bill_line.move_id 
                    join product_product product on product.id = bill_line.product_id 
                    join product_template product_tem on product_tem.id = product.product_tmpl_id
                    """
        where_clause = []
        where_clause.append("""bill.move_type = 'in_invoice'""")
        if len(self.env.companies) > 1:
            where_clause.append(f"""bill.company_id in {str(tuple(self.env.companies.ids))}""")
        else:
            where_clause.append(f"""bill.company_id = {self.env.companies[0].id}""")
        if self.date_from:
            where_clause.append(f"""bill.invoice_date >= '{self.date_from}'""")
        if self.date_to:
            where_clause.append(f"""bill.invoice_date <= '{self.date_to}'""")
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(f"""bill_line.product_id = {self.product_id[0].id}""")
            else:
                where_clause.append(f"""bill_line.product_id in {str(tuple(self.product_id.ids))}""")
        if self.contact_ids:
            if len(self.contact_ids) == 1:
                where_clause.append(f"""bill.partner_id = {self.contact_ids[0].id}""")
            else:
                where_clause.append(f"""bill.partner_id in {str(tuple(self.contact_ids.ids))}""")
        if self.bill_ids:
            if len(self.bill_ids) == 1:
                where_clause.append(f"""bill.id = {self.bill_ids[0].id}""")
            else:
                where_clause.append(f"""bill.id in {str(tuple(self.bill_ids.ids))}""")
        if where_clause:
            query += " where " + ' and '.join(where_clause)
        self.env.cr.execute(query)
    def _sql_delivery_note(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,scheduled_date,delivery_reference,delivery_note_id,order_reference,partner_id,
                    carrier_tracking_ref,barcode,description,location_id,price_unit,quantity,company_id,
                    picking_state)

                select
                    {report_id} AS report_id,
                    picking.scheduled_date as scheduled_date,
                    picking.name as delivery_reference,
                    picking.id as delivery_note_id,
                    picking.origin as order_reference,
                    picking.partner_id as partner_id,
                    picking.carrier_tracking_ref as carrier_tracking_ref,
                    product.barcode as barcode,
                    product_tem.name as description,
                    picking.location_id as location_id,
                    s_line.price_unit as price_unit,
                    (select sum(qty_done) from stock_move_line where move_id = move.id) as quantity,
                    picking.company_id as company_id,
                    picking.state as picking_state
                    from stock_move move
                    join stock_picking picking on picking.id = move.picking_id 
                    join product_product product on product.id = move.product_id 
                    join product_template product_tem on product_tem.id = product.product_tmpl_id
                    join sale_order_line s_line on s_line.id = move.sale_line_id
                    join stock_picking_type picking_type on picking_type.id = picking.picking_type_id
                    """
        where_clause = []
        where_clause.append("""picking_type.code = 'outgoing'""")
        where_clause.append("""picking.name like 'DN%'""")
        if len(self.env.companies) > 1:
            where_clause.append(f"""picking.company_id in {str(tuple(self.env.companies.ids))}""")
        else:
            where_clause.append(f"""picking.company_id = {self.env.companies[0].id}""")
        if self.date_from:
            where_clause.append(f"""picking.scheduled_date >= '{self.date_from.strftime('%Y-%m-%d') + ' 00:00:00'}'""")
        if self.date_to:
            where_clause.append(f"""picking.scheduled_date <= '{self.date_to.strftime('%Y-%m-%d') + ' 23:59:59'}'""")
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(f"""move.product_id = {self.product_id[0].id}""")
            else:
                where_clause.append(f"""move.product_id in {str(tuple(self.product_id.ids))}""")
        if self.contact_ids:
            if len(self.contact_ids) == 1:
                where_clause.append(f"""picking.partner_id = {self.contact_ids[0].id}""")
            else:
                where_clause.append(f"""picking.partner_id in {str(tuple(self.contact_ids.ids))}""")
        if self.delivery_note_ids:
            if len(self.delivery_note_ids) == 1:
                where_clause.append(f"""picking.id = {self.delivery_note_ids[0].id}""")
            else:
                where_clause.append(f"""picking.id in {str(tuple(self.delivery_note_ids.ids))}""")
        if where_clause:
            query += " where " + ' and '.join(where_clause)
        self.env.cr.execute(query)

    def _sql_vendor_credit(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,invoice_date,invoice_number,invoice_id,partner_id,bill_reference,rma_id,barcode,
                    description,price_unit,quantity,
                    price_subtotal,company_id,invoice_state,currency_id)

                select
                    {report_id} AS report_id,
                    invoice.invoice_date as invoice_date,
                    invoice.name as invoice_number,
                    invoice.id as invoice_id,
                    invoice.partner_id as partner_id,
                    invoice.ref as bill_reference,
                    invoice.rma_id as rma_id,
                    product.barcode as barcode,
                    product_tem.name as description,
                    invoice_line.price_unit as price_unit,
                    invoice_line.quantity as quantity,
                    invoice_line.price_subtotal as price_subtotal,
                    invoice.company_id as company_id,
                    invoice.state as invoice_state,
                    invoice.currency_id as currency_id
                    from account_move_line invoice_line
                    join account_move invoice on invoice.id = invoice_line.move_id
                    join product_product product on product.id = invoice_line.product_id
                    join product_template product_tem on product_tem.id = product.product_tmpl_id
                    """
        where_clause = []
        where_clause.append("""invoice.move_type = 'in_refund'""")
        if len(self.env.companies) > 1:
            where_clause.append(f"""invoice.company_id in {str(tuple(self.env.companies.ids))}""")
        else:
            where_clause.append(f"""invoice.company_id = {self.env.companies[0].id}""")
        if self.date_from:
            where_clause.append(f"""invoice.invoice_date >= '{self.date_from}'""")
        if self.date_to:
            where_clause.append(f"""invoice.invoice_date <= '{self.date_to}'""")
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(f"""invoice_line.product_id = {self.product_id[0].id}""")
            else:
                where_clause.append(f"""invoice_line.product_id in {str(tuple(self.product_id.ids))}""")
        if self.contact_ids:
            if len(self.contact_ids) == 1:
                where_clause.append(f"""invoice.partner_id = {self.contact_ids[0].id}""")
            else:
                where_clause.append(f"""invoice.partner_id in {str(tuple(self.contact_ids.ids))}""")
        if self.vendor_credit_ids:
            if len(self.vendor_credit_ids) == 1:
                where_clause.append(f"""invoice.id = {self.vendor_credit_ids[0].id}""")
            else:
                where_clause.append(f"""invoice.id in {str(tuple(self.vendor_credit_ids.ids))}""")
        if where_clause:
            query += " where " + ' and '.join(where_clause)
        self.env.cr.execute(query)

    def _sql_grn(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,scheduled_date,delivery_reference,delivery_note_id,order_reference,partner_id,
                    customer_name,customer_sales_order,carrier_tracking_ref,barcode,description,location_id,
                    company_id,quantity,picking_state,grn_tracking_number_id,landed_cost_line_id)

                select
                    {report_id} AS report_id,
                    picking.scheduled_date as scheduled_date,
                    picking.name as delivery_reference,
                    picking.id as delivery_note_id,
                    picking.origin as order_reference,
                    picking.partner_id as partner_id,
                    p_line.customer_name as customer_name,
                    p_line.customer_sales_order as customer_sales_order,
                    picking.carrier_tracking_ref as carrier_tracking_ref,
                    product.barcode as barcode,
                    product_tem.name as description,
                    picking.location_dest_id as location_id,
                    picking.company_id as company_id,
                    (select sum(qty_done) from stock_move_line where move_id = move.id) as quantity,
                    picking.state as picking_state,
                    picking.grn_tracking_number_id as grn_tracking_number_id,
                    landed_cost_line.id as landed_cost_line_id
                    from stock_move move
                    join stock_picking picking on picking.id = move.picking_id 
                    join product_product product on product.id = move.product_id 
                    join product_template product_tem on product_tem.id = product.product_tmpl_id
                    join purchase_order_line p_line on p_line.id = move.purchase_line_id
                    join stock_picking_type picking_type on picking_type.id = picking.picking_type_id
                    left join stock_landed_cost_stock_picking_rel stock_landed_cost_stock_picking on stock_landed_cost_stock_picking.stock_picking_id = picking.id
                    left join landed_cost_valuation_lines landed_cost_line on landed_cost_line.cost_id = stock_landed_cost_stock_picking.stock_landed_cost_id and landed_cost_line.product_id = product.id

                    """
        where_clause = []
        where_clause.append("""picking_type.code = 'incoming'""")
        where_clause.append("""picking.name like 'GRN%'""")
        if len(self.env.companies) > 1:
            where_clause.append(f"""picking.company_id in {str(tuple(self.env.companies.ids))}""")
        else:
            where_clause.append(f"""picking.company_id = {self.env.companies[0].id}""")
        if self.date_from:
            where_clause.append(f"""picking.scheduled_date >= '{self.date_from.strftime('%Y-%m-%d') + ' 00:00:00'}'""")
        if self.date_to:
            where_clause.append(f"""picking.scheduled_date <= '{self.date_to.strftime('%Y-%m-%d') + ' 23:59:59'}'""")
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(f"""move.product_id = {self.product_id[0].id}""")
            else:
                where_clause.append(f"""move.product_id in {str(tuple(self.product_id.ids))}""")
        if self.contact_ids:
            if len(self.contact_ids) == 1:
                where_clause.append(f"""picking.partner_id = {self.contact_ids[0].id}""")
            else:
                where_clause.append(f"""picking.partner_id in {str(tuple(self.contact_ids.ids))}""")
        if self.grn_ids:
            if len(self.grn_ids) == 1:
                where_clause.append(f"""picking.id = {self.grn_ids[0].id}""")
            else:
                where_clause.append(f"""picking.id in {str(tuple(self.grn_ids.ids))}""")
        if where_clause:
            query += " where " + ' and '.join(where_clause)
        self.env.cr.execute(query)

    def _sql_inventory_adjustment(self, report_id):

        query = f"""
                INSERT INTO history_report
                    (report_id,date,reference,product_id,barcode,description,location_id,
                    location_dest_id,quantity,company_id,stock_move_line_state)

                select
                    {report_id} AS report_id,
                    s_move_line.date as date,
                    s_move_line.reference as reference,
                    product.id as product_id,
                    product.barcode as barcode,
                    product_tem.name as description,
                    s_move_line.location_id as location_id,
                    s_move_line.location_dest_id as location_dest_id,
                    s_move_line.qty_done as quantity,
                    s_move_line.company_id as company_id,
                    s_move_line.state as stock_move_line_state
                    from stock_move_line s_move_line
                    join product_product product on product.id = s_move_line.product_id
                    join product_template product_tem on product_tem.id = product.product_tmpl_id
                    join stock_location loc ON loc.usage = 'inventory' and (loc.id = s_move_line.location_id  or loc.id = s_move_line.location_dest_id)
                    """

        where_clause = []
        if len(self.env.companies) > 1:
            where_clause.append(f"""s_move_line.company_id in {str(tuple(self.env.companies.ids))}""")
        else:
            where_clause.append(f"""s_move_line.company_id = {self.env.companies[0].id}""")
        if self.date_from:
            where_clause.append(f"""s_move_line.date >= '{self.date_from.strftime('%Y-%m-%d') + ' 00:00:00'}'""")
        if self.date_to:
            where_clause.append(f"""s_move_line.date <= '{self.date_to.strftime('%Y-%m-%d') + ' 23:59:59'}'""")
        if self.product_id:
            if len(self.product_id) == 1:
                where_clause.append(f"""s_move_line.product_id = {self.product_id[0].id}""")
            else:
                where_clause.append(f"""s_move_line.product_id in {str(tuple(self.product_id.ids))}""")
        if where_clause:
            query += ' where ' + ' and '.join(where_clause)
        self.env.cr.execute(query)

    def _compute_data(self,report_id):
        # Priya We need to delete the report because is always creates new records 29/01/2024
        query = "DELETE from history_report;"
        self.env.cr.execute(query)
        if self.transaction_type == 'sale_order':
            self._sql_sale_order(report_id)
        elif self.transaction_type == 'invoices':
            self._sql_invoices(report_id)
        elif self.transaction_type == 'purchase_order':
            self._sql_purchase_order(report_id)
        elif self.transaction_type == 'credit_note':
            self._sql_credit_note(report_id)
        elif self.transaction_type == 'bills':
            self._sql_bills(report_id)
        elif self.transaction_type == 'delivery_note':
            self._sql_delivery_note(report_id)
        elif self.transaction_type == 'vendor_credit':
            self._sql_vendor_credit(report_id)
        elif self.transaction_type == 'grn':
            self._sql_grn(report_id)
        elif self.transaction_type == 'inventory_adjustment':
            self._sql_inventory_adjustment(report_id)
        # self.refresh()

    def action_view_record(self):
        self.ensure_one()
        report_id = self.env['res.history.report'].create({}).id
        self._compute_data(report_id)
        print ("sddohIODQWQ",self._compute_data(report_id))
        view = False
        name= ''
        if self.transaction_type == 'sale_order':
            if self.env.user.has_group('sales_team.group_sale_salesman'):
                name='Sale Order'
                view = self.env.ref('panworld_history.history_report_view_tree')
            else:
                raise UserError(_('User do not have access to Sale Order. Please contact Administrator.'))
        elif self.transaction_type == 'invoices':
            if self.env.user.has_group('account.group_account_readonly') or self.env.user.has_group('account.group_account_invoice'):
                name = 'Invoices'
                print ("reporttttttttttttt",report_id)
                view = self.env.ref('panworld_history.history_report_invoice_view_tree')
            else:
                raise UserError(_('User do not have access to Accounting. Please contact Administrator.'))
        elif self.transaction_type == 'purchase_order':
            if self.env.user.has_group('purchase.group_purchase_user'):
                name = 'Purchase Order'
                view = self.env.ref('panworld_history.history_report_purchase_view_tree')
            else:
                raise UserError(_('User do not have access to Purchase Order. Please contact Administrator.'))
        elif self.transaction_type == 'credit_note':
            if self.env.user.has_group('account.group_account_readonly') or self.env.user.has_group(
                    'account.group_account_invoice'):
                name = 'Credit Note'
                view = self.env.ref('panworld_history.history_report_credit_note_view_tree')
            else:
                raise UserError(_('User do not have access to Accounting. Please contact Administrator.'))
        elif self.transaction_type == 'bills':
            if self.env.user.has_group('account.group_account_readonly') or self.env.user.has_group(
                    'account.group_account_invoice'):
                name = 'Bill'
                view = self.env.ref('panworld_history.history_report_bill_view_tree')
            else:
                raise UserError(_('User do not have access to Accounting. Please contact Administrator.'))
        elif self.transaction_type == 'delivery_note':
            if self.env.user.has_group('stock.group_stock_user'):
                name = 'Delivery Note'
                view = self.env.ref('panworld_history.history_report_delivery_note_view_tree')
            else:
                raise UserError(_('User do not have access to Inventory. Please contact Administrator.'))
        elif self.transaction_type == 'vendor_credit':
            if self.env.user.has_group('account.group_account_readonly') or self.env.user.has_group(
                    'account.group_account_invoice'):
                name = 'Vendor Credit'
                view = self.env.ref('panworld_history.history_report_vendor_credit_view_tree')
            else:
                raise UserError(_('User do not have access to Accounting. Please contact Administrator.'))
        elif self.transaction_type == 'grn':
            if self.env.user.has_group('stock.group_stock_user'):
                name = 'GRN'
                view = self.env.ref('panworld_history.history_report_grn_view_tree')
            else:
                raise UserError(_('User do not have access to Inventory. Please contact Administrator.'))
        elif self.transaction_type == 'inventory_adjustment':
            if self.env.user.has_group('stock.group_stock_user'):
                name = 'Inventory Adjustment'
                view = self.env.ref('panworld_history.history_report_inventory_adjustment_view_tree')
            else:
                raise UserError(_('User do not have access to Inventory. Please contact Administrator.'))
        else:
            raise UserError("No data")


        view_id = view and view.id or False
        context = dict(self.env.context or {})

        return {
            'name': name,
            'view_mode': 'list',
            'views': [(view_id, 'list')],
            'res_model': 'history.report',
            'type': 'ir.actions.act_window',
            'domain': [('report_id', '=',report_id)],
            'target': 'current',
            'context': context,
        }

    def action_remove_doc_records(self):
        if self.transaction_type == 'purchase_order' and self.purchase_order_ids:
            self.purchase_order_ids = [(6,0,[])]

        elif self.transaction_type == 'sale_order' and self.sale_order_ids:
            self.sale_order_ids = [(6,0,[])]

        elif self.transaction_type == 'invoices' and self.invoice_ids:
            self.invoice_ids = [(6,0,[])]

        elif self.transaction_type == 'bills' and self.bill_ids:
            self.bill_ids = [(6,0,[])]

        elif self.transaction_type == 'credit_note' and self.credit_note_ids:
            self.credit_note_ids = [(6,0,[])]

        elif self.transaction_type == 'vendor_credit' and self.vendor_credit_ids:
            self.vendor_credit_ids = [(6,0,[])]

        elif self.transaction_type == 'grn' and self.grn_ids:
            self.grn_ids = [(6,0,[])]

        elif self.transaction_type == 'delivery_note' and self.delivery_note_ids:
            self.delivery_note_ids = [(6,0,[])]
