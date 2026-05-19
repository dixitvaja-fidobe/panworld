# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import UserError
import xlsxwriter
import os
import tempfile
import base64
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class wizard_stock_ageing_report(models.TransientModel):
    _name = 'wizard.stock.ageing.report'
    _description = "Stock Ageing Report"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id, domain="[('id', 'in', allowed_company_ids)]")
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    location_ids = fields.Many2many('stock.location', string='Location', required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    start_date = fields.Date(string="As of Date", default=fields.Date.context_today)
    filter_by = fields.Selection([('product', 'Product'), ('category', 'Category')], string="Filter By")
    group_by_categ = fields.Boolean(string="Group By Category")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)
    data = fields.Binary(string='File', readonly=True)
    product_ids = fields.Many2many('product.product', string="Products")
    category_ids = fields.Many2many('product.category', string="Categories")

    @api.onchange('company_id')
    def onchange_company_id(self):
        domain = [('id', 'in', self.env.companies.ids)]
        if self.company_id:
            self.warehouse_ids = False
            self.location_ids = False
        return {'domain':{'company_id':domain}}

    @api.onchange('warehouse_ids')
    def onchange_warehouse_ids(self):
        stock_location_obj = self.env['stock.location']
        addtional_ids = []
        if self.warehouse_ids:
            for warehouse in self.warehouse_ids:
                locations = stock_location_obj.search([('location_id', 'child_of', warehouse.view_location_id.id), ('usage', '=', 'internal')])
                addtional_ids.extend(locations.ids)
            
        self.location_ids = False
        return {'domain':{'location_ids':[('id', 'in', addtional_ids)]}}

    @api.onchange('filter_by')
    def onchange_filter_by(self):
        self.product_ids = False
        self.category_ids = False

    def print_report(self):
        periods = self.get_periods()
        datas = {'form':
                    {
                        'company_id': self.company_id.id,
                        'warehouse_ids': [y.id for y in self.warehouse_ids],
                        'location_ids': self.location_ids.ids or False,
                        'start_date': self.start_date,
                        'id': self.id,
                        'product_ids': self.product_ids.ids,
                        'product_categ_ids': self.category_ids.ids,
                        'period':periods
                    },
                }
        return self.env.ref('eq_stock_ageing_report.action_stock_ageing_template').report_action(self, data=datas)

    def get_periods(self):
        periods = {}
        start_date = fields.Date.from_string(self.start_date)
        
        slabs = [
            (0, 30, '0-30'),
            (30, 60, '30-60'),
            (60, 90, '60-90'),
            (90, 120, '90-120'),
            (120, 150, '120-150'),
            (150, 180, '150-180'),
            (180, 365, '180-365'),
            (365, None, '365+'),
        ]
        
        for i, (day_start, day_stop, name) in enumerate(slabs):
            # stop_dt is the newer date (closer to start_date)
            # start_dt is the older date
            stop_dt = start_date - relativedelta(days=day_start)
            start_dt = False
            if day_stop:
                start_dt = start_date - relativedelta(days=day_stop)
                # Adjust stop date if it's not the very first bucket to avoid overlap
                if day_start != 0:
                    stop_dt = stop_dt - relativedelta(days=1)
            else:
                # For the last bucket (365+), stop is start_date - 366 days
                stop_dt = start_date - relativedelta(days=day_start + 1)
            
            periods[str(i)] = {
                'name': name,
                'stop': stop_dt.strftime('%Y-%m-%d'),
                'start': start_dt.strftime('%Y-%m-%d') if start_dt else False,
            }
        return periods

    def go_back(self):
        self.state = 'choose'
        return {
            'name': 'Stock Ageing Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def print_xls_report(self):
        xls_filename = 'Stock Ageing Report.xlsx'
        file_path = tempfile.mktemp(suffix='.xlsx')
        workbook = xlsxwriter.Workbook(file_path, {'constant_memory': True})
        report_stock_inv_obj = self.env['report.eq_stock_ageing_report.stock_ageing_report']

        header_merge_format = workbook.add_format({'bold':True, 'align':'center', 'valign':'vcenter', \
                                            'font_size':10, 'bg_color':'#D3D3D3', 'border':1})

        header_data_format = workbook.add_format({'align':'center', 'valign':'vcenter', \
                                                   'font_size':10, 'border':1})

        product_header_format = workbook.add_format({'valign':'vcenter', 'font_size':10, 'border':1})

        periods = self.get_periods()
        num_periods = len(periods)
        sorted_period_keys = sorted(periods.keys(), reverse=True) # newest to oldest

        for warehouse in self.warehouse_ids:
            worksheet = workbook.add_worksheet(warehouse.name)
            worksheet.merge_range(0, 0, 2, num_periods + 3, "Stock Ageing Report", header_merge_format)

            worksheet.set_column(0, 1, 18)
            worksheet.set_column(2, num_periods + 3, 12)
            worksheet.write(5, 0, 'Company', header_merge_format)
            worksheet.write(5, 1, 'Warehouse', header_merge_format)
            worksheet.write(5, 2, 'As of Date', header_merge_format)

            worksheet.write(6, 0, self.company_id.name, header_data_format)
            worksheet.write(6, 1, warehouse.name, header_data_format)
            worksheet.write(6, 2, self.start_date.strftime('%d-%m-%Y'), header_data_format)

            col = 1
            if not self.location_ids:
                worksheet.merge_range(9, 0, 9, 1, "Products", header_merge_format)
                for key in sorted_period_keys:
                    col += 1
                    worksheet.write(9, col, periods[key]['name'], header_merge_format)
                worksheet.write(9, col + 1, "Total", header_merge_format)

                rows = 10
                sum_columns = {key: 0.00 for key in sorted_period_keys}
                sum_total_qty = 0.00
                if not self.group_by_categ:
                    products = report_stock_inv_obj._get_products(self)
                    # Process in batches of 500 to prevent MemoryError
                    batch_size = 500
                    product_ids = products.ids
                    
                    for i in range(0, len(product_ids), batch_size):
                        batch_ids = product_ids[i:i + batch_size]
                        batch_products = self.env['product.product'].browse(batch_ids)
                        # Pre-fetch read for efficiency
                        product_names = {p['id']: p['display_name'] for p in batch_products.search_read([('id', 'in', batch_ids)], ['display_name'])}
                        
                        ageing_inventory_data = report_stock_inv_obj._get_ageing_inventory_bulk(self, batch_products, warehouse, periods)
                        
                        for product_id in batch_ids:
                            product_val = ageing_inventory_data.get(product_id, {i: 0.0 for i in range(num_periods)})
                            product_val['total_qty'] = sum(product_val[i] for i in range(num_periods))
                            total_qty = product_val.get('total_qty')
                            name = product_names.get(product_id, 'Unknown')

                            worksheet.merge_range(rows, 0, rows, 1, name, product_header_format)
                            col = 1
                            for key in sorted_period_keys:
                                col += 1
                                val = product_val.get(int(key), 0.0)
                                worksheet.write(rows, col, val, header_data_format)
                                sum_columns[key] += val

                            worksheet.write(rows, col + 1, total_qty, header_data_format)
                            sum_total_qty += total_qty
                            rows += 1

                    worksheet.merge_range(rows + 1, 0, rows + 1, 1, 'Total', header_merge_format)
                    col = 1
                    for key in sorted_period_keys:
                        col += 1
                        worksheet.write(rows + 1, col, sum_columns[key], header_merge_format)
                    worksheet.write(rows + 1, col + 1, sum_total_qty, header_merge_format)

                else:
                    rows += 1
                    for category in report_stock_inv_obj._get_product_category(self):
                        products = report_stock_inv_obj._get_products(self, category)
                        if products:
                            # Pre-calculate category totals
                            sum_categ_columns = {key: 0.00 for key in sorted_period_keys}
                            sum_categ_total_qty = 0.00
                            
                            worksheet.merge_range(rows, 0, rows, num_periods + 2, category.name, header_merge_format)
                            rows += 1
                            
                            # Batch process category products
                            batch_size = 500
                            product_ids = products.ids
                            for i in range(0, len(product_ids), batch_size):
                                batch_ids = product_ids[i:i + batch_size]
                                batch_products = self.env['product.product'].browse(batch_ids)
                                product_names = {p['id']: p['display_name'] for p in batch_products.search_read([('id', 'in', batch_ids)], ['display_name'])}
                                ageing_inventory_data = report_stock_inv_obj._get_ageing_inventory_bulk(self, batch_products, warehouse, periods)
                                
                                for product_id in batch_ids:
                                    product_val = ageing_inventory_data.get(product_id, {i: 0.0 for i in range(num_periods)})
                                    product_val['total_qty'] = sum(product_val[i] for i in range(num_periods))
                                    total_qty = product_val.get('total_qty')
                                    name = product_names.get(product_id, 'Unknown')

                                    worksheet.merge_range(rows, 0, rows, 1, name, product_header_format)
                                    col = 1
                                    for key in sorted_period_keys:
                                        col += 1
                                        val = product_val.get(int(key), 0.0)
                                        worksheet.write(rows, col, val, header_data_format)
                                        sum_categ_columns[key] += val
                                        sum_columns[key] += val

                                    worksheet.write(rows, col + 1, total_qty, header_data_format)
                                    sum_categ_total_qty += total_qty
                                    sum_total_qty += total_qty
                                    rows += 1

                            # Writing Categ Total row
                            worksheet.merge_range(rows, 0, rows, 1, 'Total', header_merge_format)
                            col = 1
                            for key in sorted_period_keys:
                                col += 1
                                worksheet.write(rows, col, sum_categ_columns[key], header_merge_format)
                            worksheet.write(rows, col + 1, sum_categ_total_qty, header_merge_format)
                            rows += 2
            else:
                worksheet.merge_range(9, 0, 9, 1, "Products", header_merge_format)
                worksheet.write(9, 2, "Location", header_merge_format)
                col = 2
                for key in sorted_period_keys:
                    col += 1
                    worksheet.write(9, col, periods[key]['name'], header_merge_format)
                worksheet.write(9, col + 1, "Total", header_merge_format)

                rows = 10
                sum_columns = {key: 0.00 for key in sorted_period_keys}
                sum_total_qty = 0.00
                location_ids = report_stock_inv_obj.get_warehouse_wise_location(self, warehouse)
                if not self.group_by_categ:
                    product_recs = report_stock_inv_obj._get_products(self)
                    product_ids = product_recs.ids
                    
                    batch_size = 500
                    for i in range(0, len(product_ids), batch_size):
                        batch_ids = product_ids[i:i + batch_size]
                        batch_products = self.env['product.product'].browse(batch_ids)
                        product_names = {p['id']: p['display_name'] for p in batch_products.sudo().search_read([('id', 'in', batch_ids)], ['display_name'])}
                        ageing_locations_data = report_stock_inv_obj._get_ageing_inventory_locations_bulk(self, batch_products, warehouse, location_ids, periods)
                        
                        for product in batch_products:
                            location_wise_data = report_stock_inv_obj.get_location_wise_product(self, warehouse, product, location_ids, periods, bulk_data=ageing_locations_data)
                            total_qty = location_wise_data[1][-1]
                            
                            if total_qty == 0: # Skip products with zero stock
                                continue
                                
                            name = product_names.get(product.id, 'Unknown')
                            
                            worksheet.merge_range(rows, 0, rows, 1, name, product_header_format)
                            worksheet.write(rows, 2, '', header_data_format)
                            col = 2
                            for idx, key in enumerate(sorted_period_keys):
                                col += 1
                                val = location_wise_data[1][idx]
                                worksheet.write(rows, col, val, header_merge_format)
                                sum_columns[key] += val
                            worksheet.write(rows, col + 1, total_qty, header_merge_format)
                            sum_total_qty += total_qty
                            rows += 1

                            for location, value in location_wise_data[0].items():
                                if value.get('total_qty', 0.0) != 0: # Only show non-zero locations
                                    worksheet.merge_range(rows, 0, rows, 1, '', header_data_format)
                                    worksheet.write(rows, 2, location.display_name, header_data_format)
                                    col = 2
                                    for key in sorted_period_keys:
                                        col += 1
                                        val = value.get(int(key), 0.0)
                                        worksheet.write(rows, col, val, header_data_format)
                                    worksheet.write(rows, col + 1, value['total_qty'], header_data_format)
                                    rows += 1

                    rows += 1
                    worksheet.merge_range(rows, 0, rows, 1, 'Total', header_merge_format)
                    worksheet.write(rows, 2, '', header_merge_format)
                    col = 2
                    for key in sorted_period_keys:
                        col += 1
                        worksheet.write(rows, col, sum_columns[key], header_merge_format)
                    worksheet.write(rows, col + 1, sum_total_qty, header_merge_format)

                else:
                    for category in report_stock_inv_obj._get_product_category(self):
                        worksheet.merge_range(rows, 0, rows, num_periods + 3, category.name, header_merge_format)
                        rows += 1
                        sum_categ_columns = {key: 0.00 for key in sorted_period_keys}
                        sum_categ_total_qty = 0.00
                        product_recs = report_stock_inv_obj._get_products(self, category)
                        product_ids = product_recs.ids
                        
                        batch_size = 500
                        for i in range(0, len(product_ids), batch_size):
                            batch_ids = product_ids[i:i + batch_size]
                            batch_products = self.env['product.product'].browse(batch_ids)
                            product_names = {p['id']: p['display_name'] for p in batch_products.sudo().search_read([('id', 'in', batch_ids)], ['display_name'])}
                            ageing_locations_data = report_stock_inv_obj._get_ageing_inventory_locations_bulk(self, batch_products, warehouse, location_ids, periods)

                            for product in batch_products:
                                location_wise_data = report_stock_inv_obj.get_location_wise_product(self, warehouse, product, location_ids, periods, bulk_data=ageing_locations_data)
                                total_qty = location_wise_data[1][-1]
                                
                                if total_qty == 0: # Skip products with zero stock
                                    continue
                                    
                                name = product_names.get(product.id, 'Unknown')

                                worksheet.merge_range(rows, 0, rows, 1, name, product_header_format)
                                worksheet.write(rows, 2, '', header_data_format)
                                col = 2
                                for idx, key in enumerate(sorted_period_keys):
                                    col += 1
                                    val = location_wise_data[1][idx]
                                    worksheet.write(rows, col, val, header_merge_format)
                                    sum_categ_columns[key] += val
                                    sum_columns[key] += val
                                worksheet.write(rows, col + 1, total_qty, header_merge_format)
                                sum_categ_total_qty += total_qty
                                sum_total_qty += total_qty
                                rows += 1

                                for location, value in location_wise_data[0].items():
                                    if value.get('total_qty', 0.0) != 0:
                                        worksheet.merge_range(rows, 0, rows, 1, '', header_data_format)
                                        worksheet.write(rows, 2, location.display_name, header_data_format)
                                        col = 2
                                        for key in sorted_period_keys:
                                            col += 1
                                            val = value.get(int(key), 0.0)
                                            worksheet.write(rows, col, val, header_data_format)
                                        worksheet.write(rows, col + 1, value['total_qty'], header_data_format)
                                        rows += 1

                        worksheet.merge_range(rows, 0, rows, 1, "Total", header_merge_format)
                        worksheet.write(rows, 2, '', header_merge_format)
                        col = 2
                        for key in sorted_period_keys:
                            col += 1
                            worksheet.write(rows, col, sum_categ_columns[key], header_merge_format)
                        worksheet.write(rows, col + 1, sum_categ_total_qty, header_merge_format)
                        rows += 2
                    
                    worksheet.merge_range(rows, 0, rows, 1, 'Grand Total', header_merge_format)
                    worksheet.write(rows, 2, '', header_merge_format)
                    col = 2
                    for key in sorted_period_keys:
                        col += 1
                        worksheet.write(rows, col, sum_columns[key], header_merge_format)
                    worksheet.write(rows, col + 1, sum_total_qty, header_merge_format)

        workbook.close()
        
        with open(file_path, 'rb') as f:
            file_data = base64.b64encode(f.read())
            
        self.write({
            'state': 'get',
            'data': file_data,
            'name': xls_filename
        })
        
        try:
            os.remove(file_path)
        except Exception:
            pass

        return {
            'name': 'Stock Ageing Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: