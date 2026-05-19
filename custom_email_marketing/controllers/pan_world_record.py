# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import http
from odoo.http import request, Response

class CreatePanWorld(http.Controller):

    @http.route('/create_pan_world_record', auth='public', methods=['POST', 'OPTIONS'], csrf=False, type='json', website=True, sitemap=False, cors="*")
    def create_pan_world_record(self, **kwargs):
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }

        if request.httprequest.method == 'OPTIONS':
            return Response(status=200, headers=headers)

        get_value = request.jsonrequest
        get_country = get_value.get('country')
        res_country_id = request.env['res.country'].sudo().search([('name', '=', get_country)], limit=1)
        pan_world_records = request.env['mailing.contact'].sudo().search([('email', '=', get_value.get('email'))], limit=1)

        if pan_world_records:
            pan_world_records.write({
                'name': get_value.get('name'),
                'mobile_no': get_value.get('mobile_number'),
                'school_name': get_value.get('school_name'),
                'country_id': res_country_id.id,
                'region_name': get_value.get('city'),
                'interest': get_value.get('notes'),
            })
            response_data = {'status': 'success', 'id': pan_world_records.id}
            status_code = 200
        else:
            pan_world_id = request.env['mailing.contact'].sudo().create({
                'name': get_value.get('name'),
                'email': get_value.get('email'),
                'mobile_no': get_value.get('mobile_number'),
                'school_name': get_value.get('school_name'),
                'country_id': res_country_id.id,
                'region_name': get_value.get('city'),
                'interest': get_value.get('notes'),
            })
            response_data = {'status': 'success', 'id': pan_world_id.id}
            status_code = 200

        return Response(response_data, status=status_code, headers=headers)
