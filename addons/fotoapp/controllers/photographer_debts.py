import logging

from odoo import http
from odoo.http import request

from .portal_base import PhotographerPortalMixin

_logger = logging.getLogger(__name__)


class PhotographerDebtController(PhotographerPortalMixin, http.Controller):

    @http.route(['/mi/fotoapp/deudas'], type='http', auth='user', website=True)
    def photographer_debts(self, **kwargs):
        partner, denied = self._ensure_photographer()
        if not partner:
            return denied

        Debt = request.env['fotoapp.debt'].sudo()
        partner_ids = {partner.id}
        if partner.commercial_partner_id:
            partner_ids.add(partner.commercial_partner_id.id)
        domain = [('partner_id', 'in', list(partner_ids))]
        active_debts = Debt.search(domain + [('state', 'in', ['pending', 'in_grace'])],
                                   order='due_date asc')
        paid_debts = Debt.search(domain + [('state', '=', 'paid')], order='paid_date desc', limit=50)
        values = {
            'partner': partner,
            'active_debts': active_debts,
            'paid_debts': paid_debts,
            'active_menu': 'debts',
        }
        return request.render('fotoapp.photographer_debts_page', values)

    @http.route(['/mi/fotoapp/deuda/<int:debt_id>/carrito'], type='http', auth='user', website=True)
    def add_debt_to_cart(self, debt_id, **kwargs):
        partner, denied = self._ensure_photographer()
        if not partner:
            return denied

        Debt = request.env['fotoapp.debt'].sudo()
        debt = Debt.browse(debt_id)
        if not debt or debt.partner_id != partner or not debt.can_be_paid():
            return request.not_found()

        if debt.sale_order_id and debt.sale_order_id.state in ('draft', 'sent'):
            order = debt.sale_order_id
        else:
            order = request.website.sale_get_order(force_create=1)
        if not order:
            return request.redirect('/shop/cart')

        product_variant = self._get_debt_product_variant()
        if not product_variant:
            _logger.error('No se pudo encontrar el producto de renovación para registrar la deuda.')
            return request.redirect('/shop/cart')

        # Eliminamos la línea previa si existe para mantener un único item por deuda
        if debt.sale_order_line_id and debt.sale_order_line_id.order_id == order:
            debt.sale_order_line_id.unlink()

        line_vals = {
            'order_id': order.id,
            'product_id': product_variant.id,
            'name': '%s - %s' % (debt.get_portal_label(), debt.plan_id.name or ''),
            'product_uom_qty': 1,
            'price_unit': debt.amount,
        }
        line = request.env['sale.order.line'].sudo().create(line_vals)
        debt.write({
            'sale_order_id': order.id,
            'sale_order_line_id': line.id,
        })
        return request.redirect('/shop/cart')

    def _get_debt_product_variant(self):
        template = request.env.ref('fotoapp.product_plan_renewal_template', raise_if_not_found=False)
        if not template:
            return False
        if template.product_variant_id:
            return template.product_variant_id
        return request.env['product.product'].sudo().search([('product_tmpl_id', '=', template.id)], limit=1)
