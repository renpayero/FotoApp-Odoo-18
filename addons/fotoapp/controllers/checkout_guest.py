"""Guest checkout defaults for FotoApp.

This controller forces minimal address/billing data for anonymous carts so the
checkout can proceed with only email. It is defensive: if localization models
are missing, it falls back gracefully.
"""

import logging
import re

from odoo import _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_logger = logging.getLogger(__name__)


class FotoappWebsiteSale(WebsiteSale):
	def _fotoapp_is_guest_checkout(self, order_sudo):
		return bool(order_sudo and order_sudo._is_anonymous_cart())

	def _first(self, model, domain, order=None):
		registry = request.env.registry
		if model not in registry:
			return request.env['res.partner'].browse()
		env = request.env.sudo()
		return env[model].search(domain, limit=1, order=order or 'id')

	def _fotoapp_validate_single_photographer(self, order_sudo):
		photo_lines = order_sudo.order_line.filtered(lambda l: l.foto_photographer_id)
		photographers = set(photo_lines.mapped('foto_photographer_id').ids)
		if len(photographers) > 1:
			request.session['website_sale_cart_warning'] = _(
				'No está permitido agregar fotos de varios fotógrafos al carrito. Separá los carritos por favor.'
			)
			return request.redirect('/shop/cart')
		return None

	def _validate_address_values(
		self,
		address_values,
		partner_sudo,
		address_type,
		use_delivery_as_billing,
		required_fields,
		is_main_address,
		**kwargs,
	):
		_logger.info("FotoApp Guest Checkout - Address Values before validation: %s", address_values)

		order_sudo = request.website.sale_get_order()
		is_guest = self._fotoapp_is_guest_checkout(order_sudo)

		if is_guest:
			country = self._first('res.country', [('code', '=', 'AR')]) or request.website.company_id.country_id
			state = None
			if country:
				state = self._first('res.country.state', [('country_id', '=', country.id), ('code', 'in', ['S', 'SF'])])
				if not state:
					state = self._first('res.country.state', [('country_id', '=', country.id), ('name', 'ilike', 'Santa Fe')])
				if not state:
					state = self._first('res.country.state', [('country_id', '=', country.id)])
			if not state:
				state = self._first('res.country.state', [('id', '!=', False)])

			Partner = request.env['res.partner']
			afip_id = False
			if 'l10n_ar_afip_responsibility_type_id' in Partner._fields:
				afip = self._first('afip.responsibility.type', [('name', 'ilike', 'Consumidor Final')])
				afip_id = afip.id if afip else False

			dni_id = False
			if 'l10n_latam_identification_type_id' in Partner._fields:
				dni = self._first('l10n_latam.identification.type', [('name', 'ilike', 'DNI')])
				dni_id = dni.id if dni else False

			forced = {
				'name': _('Guest Buyer'),
				'company_name': _('Guest Buyer'),
				'country_id': country.id if country else False,
				'state_id': state.id if state else False,
				'city': 'Rosario',
				'zip': '2000',
				'phone': '2477610100',
				'vat': '43026589',
				'street': 'Calle falsa 123',
				'street2': '4-1',
			}
			if afip_id:
				forced['l10n_ar_afip_responsibility_type_id'] = afip_id
			if dni_id:
				forced['l10n_latam_identification_type_id'] = dni_id

			for key, val in forced.items():
				if key in Partner._fields:
					address_values[key] = val

			email = (address_values.get('email') or '').strip()
			if not email or not EMAIL_RE.match(email):
				return set(), {'email'}, [_('Ingresá un correo válido.')]

			required_fields = ['email']
			return set(), set(), []

		return super()._validate_address_values(
			address_values,
			partner_sudo,
			address_type,
			use_delivery_as_billing,
			required_fields,
			is_main_address,
			**kwargs,
		)

	def _check_cart(self, order_sudo):
		redir = super()._check_cart(order_sudo)
		if redir:
			return redir
		return self._fotoapp_validate_single_photographer(order_sudo)

	def shop_address_submit(self, **post):
		order = request.website.sale_get_order()
		is_guest = self._fotoapp_is_guest_checkout(order)

		response = super().shop_address_submit(**post)

		if is_guest:
			location = getattr(response, 'headers', {}).get('Location') if hasattr(response, 'headers') else None
			status = getattr(response, 'status_code', None)
			if not location and status == 200:
				return request.redirect('/shop/payment')

		return response
