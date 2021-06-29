# -*- coding: utf-8 -*-
from odoo import http

# class PoLuarprop(http.Controller):
#     @http.route('/po_luarprop/po_luarprop/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/po_luarprop/po_luarprop/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('po_luarprop.listing', {
#             'root': '/po_luarprop/po_luarprop',
#             'objects': http.request.env['po_luarprop.po_luarprop'].search([]),
#         })

#     @http.route('/po_luarprop/po_luarprop/objects/<model("po_luarprop.po_luarprop"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('po_luarprop.object', {
#             'object': obj
#         })