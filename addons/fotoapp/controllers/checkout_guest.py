# -*- coding: utf-8 -*-
from odoo import _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class FotoappWebsiteSale(WebsiteSale):
    def _fotoapp_validate_single_photographer(self, order_sudo):
        photo_lines = order_sudo.order_line.filtered(lambda l: l.foto_photographer_id)
        photographers = set(photo_lines.mapped('foto_photographer_id').ids)
        if len(photographers) > 1:
            request.session['website_sale_cart_warning'] = _(
                'No está permitido agregar fotos de varios fotógrafos al carrito. Separá los carritos por favor.'
            )
            return request.redirect('/shop/cart')
        return None

    def _check_cart(self, order_sudo):
        redir = super()._check_cart(order_sudo)
        if redir:
            return redir
        return self._fotoapp_validate_single_photographer(order_sudo)
