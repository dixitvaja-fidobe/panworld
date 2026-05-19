# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import models, fields, api, _


class eq_stock_ageing_report_stock_ageing_report(models.AbstractModel):
    _name = 'report.eq_stock_ageing_report.stock_ageing_report'
    _description = "Stock Ageing Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('eq_stock_ageing_report.action_stock_ageing_template')
        record_id = data['form']['id'] if data and data['form'] and data['form']['id'] else docids[0]
        records = self.env['wizard.stock.ageing.report'].browse(record_id)
        
        # Pre-fetch ageing data for all products to avoid N+1 queries in the template
        warehouse = records.warehouse_ids[0] if records.warehouse_ids else False
        products = self._get_products(records)
        product_ids = products.ids
        
        # Pre-fetch names for efficiency
        ageing_data = self._get_ageing_inventory_bulk(records, products, warehouse, records.get_periods())
        
        return {
           'doc_model': report.model,
           'docs': records,
           'data': data,
           'get_ageing_inventory': lambda p: ageing_data.get(p.id, {i: 0.0 for i in range(len(records.get_periods()))}),
           'get_product_name': lambda p: product_names.get(p.id, 'Unknown'),
           'get_products':lambda r: products,
           'get_location_wise_product':self.get_location_wise_product,
           'get_warehouse_wise_location':self.get_warehouse_wise_location,
           'get_product_category':self._get_product_category
        }

    def get_warehouse_wise_location(self, record, warehouse):
        stock_location_obj = self.env['stock.location']
        location_ids = stock_location_obj.search([('location_id', 'child_of', warehouse.view_location_id.id)])
        final_location_ids = record.location_ids & location_ids
        return final_location_ids or location_ids

    def get_location_wise_product(self, record, warehouse, product, location_ids, periods, product_categ_id=None, bulk_data=None):
        group_by_location = {}
        sorted_keys = sorted(periods.keys(), reverse=True) # keys are index strings '0', '1', etc.
        num_periods = len(sorted_keys)
        column_totals = [0.00] * (num_periods + 1)
        
        # Use bulk_data if provided, mapping from {p_id: {l_id: {period_idx: qty}}}
        product_bulk_data = bulk_data.get(product.id, {}) if bulk_data else {}

        for location in location_ids:
            if bulk_data:
                res = product_bulk_data.get(location.id, {int(i): 0.0 for i in range(num_periods)})
                res['total_qty'] = sum(res[int(i)] for i in range(num_periods))
            else:
                res = self._get_ageing_inventory(record, product, warehouse, periods, [location.id])
            
            group_by_location[location] = res
            for i, key in enumerate(sorted_keys):
                val = res.get(int(key), 0.0)
                column_totals[i] += val
            column_totals[-1] += res.get('total_qty', 0.0)
            
        return group_by_location, column_totals

    def _get_ageing_inventory_locations_bulk(self, record, products, warehouse, locations, periods):
        product_ids = products.ids
        location_ids = locations.ids
        num_periods = len(periods)
        # Result structure: {product_id: {location_id: {period_idx: qty}}}
        res_data = {p_id: {l_id: {i: 0.0 for i in range(num_periods)} for l_id in location_ids} for p_id in product_ids}
        
        if not product_ids or not location_ids:
            return res_data

        args_list = []
        select_queries = []
        # Loop through periods to build the specific SUM(CASE...) for each bucket
        for key in sorted(periods.keys(), key=int):
            period = periods[key]
            idx = int(key)
            # stop is the newer date (upper bound), start is the older date (lower bound)
            stop_date = period.get('stop')
            start_date = period.get('start')
            
            conditions = []
            period_dates = []
            if start_date:
                conditions.append("date_only >= %s")
                period_dates.append(start_date)
            if stop_date:
                conditions.append("date_only <= %s")
                period_dates.append(stop_date)
            
            # Since the condition is used twice in the CASE, we need the dates twice.
            args_list.extend(period_dates)
            args_list.extend(period_dates)
            
            cond_str = " AND ".join(conditions) if conditions else "1=1"
            
            p_query = """
                SUM(CASE WHEN {cond} AND move_type = 'in' THEN qty ELSE 0 END) AS in_period_{idx},
                SUM(CASE WHEN {cond} AND move_type = 'out' THEN qty ELSE 0 END) AS out_period_{idx}
            """.format(cond=cond_str, idx=idx)
            select_queries.append(p_query)

        query = """
            SELECT 
                target_location_id,
                product_id,
                {select_clause}
            FROM (
                -- Treat every move as an inbound to its destination if destination is in our list
                SELECT 
                    sml.location_dest_id as target_location_id,
                    sml.product_id,
                    sml.quantity as qty,
                    'in' as move_type,
                    (sml.date::date) as date_only
                FROM stock_move_line sml
                WHERE sml.location_dest_id IN %s
                AND sml.product_id IN %s
                AND sml.state = 'done'
                
                UNION ALL
                
                -- Treat every move as an outbound from its source if source is in our list
                SELECT 
                    sml.location_id as target_location_id,
                    sml.product_id,
                    sml.quantity as qty,
                    'out' as move_type,
                    (sml.date::date) as date_only
                FROM stock_move_line sml
                WHERE sml.location_id IN %s
                AND sml.product_id IN %s
                AND sml.state = 'done'
            ) sub
            GROUP BY target_location_id, product_id
        """.format(select_clause=",".join(select_queries))
        
        # SQL arguments for the subqueries
        sub_args = [tuple(location_ids), tuple(product_ids), tuple(location_ids), tuple(product_ids)]
        # Combine args_list (period dates in SELECT) and sub_args (filters in FROM)
        # Because {select_clause} appears before the FROM clause, its arguments must come first.
        final_args = args_list + sub_args
        
        self.env.cr.execute(query, final_args)
        for row in self.env.cr.dictfetchall():
            p_id = row['product_id']
            l_id = row['target_location_id']
            if p_id in res_data and l_id in res_data[p_id]:
                # 1. Calculate Total Onhand for this Product/Location
                total_in = 0
                total_out = 0
                bucket_inbound = {}
                sorted_keys = sorted(periods.keys(), key=int) # 0 is newest, 7 is oldest
                for key in sorted_keys:
                    idx = int(key)
                    qin = float(row.get('in_period_%s' % idx) or 0.0)
                    qout = float(row.get('out_period_%s' % idx) or 0.0)
                    total_in += qin
                    total_out += qout
                    bucket_inbound[idx] = qin
                
                remaining_qty = total_in - total_out
                
                # 2. Distribute total qty into buckets using FIFO (Newest first)
                # If we have 7 units left, we check the newest bucket first.
                if remaining_qty > 0:
                    for idx in sorted_keys: # 0, 1, 2... (Newest to Oldest)
                        idx = int(idx)
                        inbound = bucket_inbound[idx]
                        if remaining_qty <= 0:
                            res_data[p_id][l_id][idx] = 0.0
                            continue
                            
                        # Take as much as possible from this bucket's inbound
                        val = min(remaining_qty, inbound)
                        # If it's the LAST bucket (oldest), put everything remaining there
                        if idx == int(sorted_keys[-1]):
                            val = remaining_qty
                            
                        res_data[p_id][l_id][idx] = val
                        remaining_qty -= val
                else:
                    # If negative stock, put it in the oldest bucket (or newest depending on preference)
                    # User said Case 2 (-3) was okay but in wrong slab. We'll put it in newest for now.
                    res_data[p_id][l_id][0] = remaining_qty
        
        return res_data

    def get_location(self, records, warehouse):
        stock_location_obj = self.env['stock.location']
        location_ids = []
        location_ids.append(warehouse.view_location_id.id)
        domain = [('company_id', '=', records.company_id.id), ('usage', '=', 'internal'), ('location_id', 'child_of', location_ids)]
        final_location_ids = stock_location_obj.search(domain).ids
        return final_location_ids

    def _get_products(self, record,category=None):
        product_product_obj = self.env['product.product']
        domain = ['|', ('type', '=', 'product'), ('is_storable', '=', True)]
        if category:
            domain += [('categ_id','=',category.id)]
        product_ids = False
        if record.category_ids and not category:
            domain.append(('categ_id', 'in', record.category_ids.ids))
            product_ids = product_product_obj.search(domain)
        if record.product_ids:
            product_ids = record.product_ids
        if not product_ids:
             product_ids = product_product_obj.search(domain)
        if category:
            product_ids = product_ids.filtered(lambda l:l.categ_id.id == category.id)
        return product_ids

    def _get_product_category(self,record):
        category_ids = False
        if record.category_ids:
            category_ids = record.category_ids
        else:
            category_ids = self.env['product.category'].search([])
        if record.product_ids:
            category_ids = category_ids.filtered(lambda l:l.id in record.product_ids.mapped('categ_id').ids)
        return category_ids

    def _get_ageing_inventory(self, record, product, warehouse, periods,location=None):
        num_periods = len(periods)
        final_dict = {i: 0.0 for i in range(num_periods)}
        final_dict['total_qty'] = 0.0
        total_qty = 0.00
        locations = location if location else self.get_location(record, warehouse)
        if not product:
            return final_dict

        product_id = product.id

        for i in range(num_periods):
            args_list = (tuple(locations), tuple(locations), tuple(locations), tuple(locations), tuple(locations), tuple(locations), tuple(locations), tuple(locations), product_id,record.company_id.id)
            dates_query = '(COALESCE(smline.date)::date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s'
                args_list += (periods[str(i)]['stop'],)

            query_res = []
            query = """
                SELECT pp.id AS product_id,pt.categ_id,

                    sum((
                    CASE WHEN spt.code in ('outgoing') AND smline.location_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory'
                    THEN -(smline.quantity * pu.factor / pu2.factor)
                    WHEN spt.code ='mrp_operation' AND smline.location_id in %s AND sourcel.usage !='inventory' AND destl.usage ='production' 
                    THEN -(smline.quantity * pu.factor / pu2.factor)
                    ELSE 0.0
                    END
                    )) AS product_qty_out,

                    sum((
                    CASE WHEN spt.code in ('incoming') AND smline.location_dest_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                    THEN (smline.quantity * pu.factor / pu2.factor)
                    WHEN spt.code = 'mrp_operation' AND smline.location_dest_id in %s AND sourcel.usage ='production' AND destl.usage !='inventory'
                    THEN (smline.quantity * pu.factor / pu2.factor)
                    ELSE 0.0 
                    END
                    )) AS product_qty_in,

                    sum((
                    CASE WHEN (spt.code ='internal') AND smline.location_dest_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                    THEN (smline.quantity * pu.factor / pu2.factor)  
                    WHEN (spt.code ='internal' OR spt.code is null) AND smline.location_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                    THEN -(smline.quantity * pu.factor / pu2.factor) 
                    ELSE 0.0 
                    END
                    )) AS product_qty_internal,

                    sum((
                    CASE WHEN sourcel.usage = 'inventory' AND smline.location_dest_id in %s  
                    THEN  (smline.quantity * pu.factor / pu2.factor)
                    WHEN destl.usage ='inventory' AND smline.location_id in %s 
                    THEN -(smline.quantity * pu.factor / pu2.factor)
                    ELSE 0.0 
                    END
                    )) AS product_qty_adjustment

                FROM product_product pp
                LEFT JOIN stock_move sm ON (sm.product_id = pp.id and sm.state = 'done')
                LEFT JOIN stock_move_line smline ON (smline.product_id = pp.id and smline.state = 'done' and smline.location_id != smline.location_dest_id and smline.move_id = sm.id)
                LEFT JOIN stock_picking_type spt ON (spt.id=sm.picking_type_id)
                LEFT JOIN stock_location sourcel ON (smline.location_id=sourcel.id)
                LEFT JOIN stock_location destl ON (smline.location_dest_id=destl.id)
                LEFT JOIN uom_uom pu ON (sm.product_uom=pu.id)
                LEFT JOIN uom_uom pu2 ON (sm.product_uom=pu2.id)
                LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                WHERE pp.id = %s and sm.company_id = %s
                AND """ + dates_query + """
                GROUP BY pt.categ_id, pp.id order by pt.categ_id
            """

            self._cr.execute(query, args_list)
            query_res = self._cr.dictfetchone()
            if query_res:
                final_qty = (query_res.get('product_qty_in') or 0.0) + (query_res.get('product_qty_out') or 0.0) + \
                    (query_res.get('product_qty_internal') or 0.0) + (query_res.get('product_qty_adjustment') or 0.0)
                final_dict[i] = final_qty
                final_dict['total_qty'] += final_qty

        return final_dict


    def _get_ageing_inventory_bulk(self, record, products, warehouse, periods, location=None):
        num_periods = len(periods)
        # get_location already identifies all internal locations for the warehouse
        locations_recs = self.env['stock.location'].browse(location if location else self.get_location(record, warehouse))
        
        if not products or not locations_recs:
            return {}

        # 1. Reuse our high-performance location-wise engine
        ageing_locations_data = self._get_ageing_inventory_locations_bulk(record, products, warehouse, locations_recs, periods)
        
        # 2. Aggregate the location data into a warehouse summary
        result = {}
        for p_id, loc_data in ageing_locations_data.items():
            product_val = {i: 0.0 for i in range(num_periods)}
            total_qty = 0.0
            
            # Sum up values from all internal locations
            for l_id, buckets in loc_data.items():
                for idx, qty in buckets.items():
                    product_val[idx] += qty
                    total_qty += qty
            
            product_val['total_qty'] = total_qty
            result[p_id] = product_val
            
        return result
