# pylint: disable=too-many-locals, ungrouped-imports
import base64
import logging
import werkzeug
from odoo import http
from odoo.tools.safe_eval import safe_eval
from odoo.addons.kw_api.controllers.controller_base import kw_api_wrapper
from odoo.addons.kw_mixin.models.datetime_extract import mining_date

from odoo.http import request

_logger = logging.getLogger(__name__)


class ApiController(http.Controller):

    @http.route(
        route='/api/fleet_vehicle_models/',
        methods=['GET'],
        auth='public',
        csrf=False,
        type='http'
    )
    @kw_api_wrapper(token=False, paginate=True, get_json=False)
    def api_fleet_vehicle_models(self, kw_api, **kw):
        models = request.env['fleet.vehicle.model'].sudo().search(
            []
        )
        return kw_api.data_response(models)

    @http.route(
        route='/api/daleth_customs_departments/',
        methods=['GET'],
        auth='public',
        csrf=False,
        type='http'
    )
    @kw_api_wrapper(token=False, paginate=True, get_json=False)
    def api_custom_departments(self, kw_api, **kw):
        departments = request.env['daleth.customs.department'].sudo().search(
            []
        )
        return kw_api.data_response(departments)

    @http.route(
        route='/api/daleth_places/checkpoint/',
        methods=['GET'],
        auth='public',
        csrf=False,
        type='http'
    )
    @kw_api_wrapper(token=False, paginate=True, get_json=False)
    def api_checkpoints(self, kw_api, **kw):
        checkpoints = request.env['daleth.place'].sudo().search(
            [('is_checkpoint', '=', True)]
        )
        return kw_api.data_response(checkpoints)

    @http.route(
        route='/api/request_stages/',
        methods=['GET'],
        auth='public',
        csrf=False,
        type='http'
    )
    @kw_api_wrapper(token=False, paginate=True, get_json=False)
    def api_request_stages_get(self, kw_api, **kw):
        stages = request.env['request.stage'].sudo().search(
            []
        )
        stages = [{
            'id': item.id,
            'name': item.name,
            'code': item.code
        } for item in stages]
        return kw_api.data_response(stages)

    @http.route(
        route='/api/requests/',
        methods=['GET'],
        auth='public',
        csrf=False,
        type='http'
    )
    @kw_api_wrapper(token=False, paginate=True, get_json=False)
    def api_requests_get(self, kw_api, **kw):
        domain = []
        for key, value in kw.items():
            if 'date' in key:
                value = mining_date(value)
                domain.append(('write_date', '>=', value))
            else:
                try:
                    domain.append((key, '=', int(value)))
                except ValueError:
                    domain.append((key, '=', value))
        requests = request.env['request.request'].sudo().search(
            domain
        )
        return kw_api.data_response(requests)

    @http.route(
        route='/api/create_request/',
        methods=['POST'],
        auth='public',
        csrf=False,
        type='http'
    )
    @kw_api_wrapper(token=False, paginate=True, get_json=False)
    def api_requests_post(self, kw_api, **kw):
        partner_info = {
            'vat': kw.get('partner_vat'),
            'name': kw.get('partner_name'),
            'street': kw.get('street'),
            'phone': kw.get('phone'),
            'mobile': kw.get('mobile'),
        }
        partner = request.env['res.partner'].sudo().search([
            ('vat', '=', partner_info.get('vat')),
            ('name', '=', partner_info.get('name')),
        ])
        if not partner:
            sovtes_type = request.env['daleth.partner.type'].sudo(
            ).search([('name', '=', 'Sovtes')], limit=1)
            partner_info['kw_partner_type_ids'] = [
                (6, None, [sovtes_type.id])
            ]
            partner_info['company_type'] = 'company'
            partner_info['requisites_ids'] = [
                (0, 0, {'enterprise_code': kw.get(
                    'enterprise_code')})
            ]
            partner = request.env['res.partner'].sudo().create(
                partner_info
            )
        service_id = kw_api.get_param_by_name(kw, 'service_id', int)
        service = request.env['request.request.line'].sudo().search([
            ('id', '=', service_id)
        ])
        vehicle = request.env['daleth.vehicle'].sudo().search([
            ('license_plate', '=', kw.get('vehicle_plate')),
        ]) or request.env['daleth.vehicle'].sudo().search([
            ('license_trailer', '=', kw.get('vehicle_trailer')),
        ])
        driver_id = kw_api.get_param_by_name(kw, 'driver_id', int)
        driver = request.env['res.partner'].sudo().search([
            ('id', '=', driver_id),
        ])
        update_req = {'partner_id': partner.id}
        update_req['vehicle_id'] = vehicle.id
        update_req['transport_id'] = kw_api.get_param_by_name(
            kw, 'transport_id', int
        ) or 100
        update_req['driver_id'] = driver.id
        update_req['vehicle_id'] = vehicle.id
        update_req['line_ids'] = [
            (4, service.id, None)
        ]
        checkpoints = safe_eval(kw.get('checkpoints'))
        update_req['kw_place_ids'] = [
            (6, None, checkpoints)
        ]
        update_req['source_address_id'] = kw_api.get_param_by_name(
            kw, 'source_address_id', int
        )
        update_req['destination_address_id'] = kw_api.get_param_by_name(
            kw, 'destination_address_id', int
        )
        update_req['entry_customs_department_id'] = kw_api.get_param_by_name(
            kw, 'entry_customs_department_id', int
        )
        update_req['departure_customs_department_id'] = \
            kw_api.get_param_by_name(
                kw, 'departure_customs_department_id', int
        )
        update_req['category_id'] = int(
            request.env['ir.config_parameter'].sudo().get_param(
                'daleth_order.daleth_order_category_id_selection')
        )
        update_req['type_id'] = int(request.env['ir.config_parameter'].sudo(
        ).get_param('daleth_order.daleth_order_type_id_selection'))
        update_req['is_daleth_order'] = True
        # => create request with defined data
        new_request = request.env['request.request'].sudo().create(
            update_req
        )
        request.env['daleth.cargo'].sudo().create({
            'name': kw.get('cargo_name'),
            'order_id': new_request.id
        })
        files = {k: v for k, v in kw.items() if isinstance(
            v, werkzeug.datastructures.FileStorage)}
        for key, value in files.items():
            name = key
            file = base64.b64encode(value.read())
            request.env['kw.document'].sudo().create({
                'model': 'request.request',
                'res_id': new_request.id,
                'company_id': request.env.user.company_id.id,
                'type_id': 404,
                'file': file,
                'name': name,
            })
        return kw_api.data_response(new_request)
