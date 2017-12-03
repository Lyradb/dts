# -*- coding: utf-8 -*-
from odoo import http

# class /home/odoo/devs/addons/dts(http.Controller):
#     @http.route('//home/odoo/devs/addons/dts//home/odoo/devs/addons/dts/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('//home/odoo/devs/addons/dts//home/odoo/devs/addons/dts/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('/home/odoo/devs/addons/dts.listing', {
#             'root': '//home/odoo/devs/addons/dts//home/odoo/devs/addons/dts',
#             'objects': http.request.env['/home/odoo/devs/addons/dts./home/odoo/devs/addons/dts'].search([]),
#         })

#     @http.route('//home/odoo/devs/addons/dts//home/odoo/devs/addons/dts/objects/<model("/home/odoo/devs/addons/dts./home/odoo/devs/addons/dts"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('/home/odoo/devs/addons/dts.object', {
#             'object': obj
#         })