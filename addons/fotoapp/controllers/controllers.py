# -*- coding: utf-8 -*-
# from odoo import http


# class Fotoapp(http.Controller):
#     @http.route('/fotoapp/fotoapp', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fotoapp/fotoapp/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fotoapp.listing', {
#             'root': '/fotoapp/fotoapp',
#             'objects': http.request.env['fotoapp.fotoapp'].search([]),
#         })

#     @http.route('/fotoapp/fotoapp/objects/<model("fotoapp.fotoapp"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fotoapp.object', {
#             'object': obj
#         })