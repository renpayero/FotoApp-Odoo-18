# -*- coding: utf-8 -*-
import logging
import re
from odoo import _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_logger = logging.getLogger(__name__)


class FotoappWebsiteSale(WebsiteSale):
    ## esto es para el checkout de invitados en FotoApp, para setear valores por defecto en la dirección
    def _fotoapp_is_guest_checkout(self, order_sudo):
        value = bool(order_sudo and order_sudo._is_anonymous_cart())
        _logger.info("FotoApp Guest Checkout - is_guest_checkout: %s", value)
        return value

    def _first(self, model, domain, order=None):
        """ORM puro: devuelve 1 registro o recordset vacío."""
        ## esto es para buscar el país, estado, etc por defecto, en el guest checkout
        registry = request.env.registry
        if model not in registry:
            return request.env['res.partner'].browse()
        return request.env[model].sudo().search(domain, limit=1, order=order or 'id')

    # def _fotoapp_apply_guest_defaults(self, address_values, order_sudo):
    #     Partner = request.env['res.partner']
    #     company = request.website.company_id.sudo()

    #     # 1) País: usar el de la compañía; si no, buscar AR; si no, cualquiera.
    #     country = company.country_id
    #     if not country:
    #         country = self._first('res.country', [('code', '=', 'AR')])
    #     if not country:
    #         country = self._first('res.country', [('id', '!=', False)])

    #     # 2) Provincia/Estado: usar el de la compañía si coincide con el país.
    #     state = company.state_id
    #     if state and country and state.country_id != country:
    #         state = request.env['res.country.state'].browse([])

    #     # Si no hay state, buscar Santa Fe (código suele ser SF; vos estabas usando 'S') el codigo es S, arreglar.

    #     if not state:
    #         dom = []
    #         if country:
    #             dom.append(('country_id', '=', country.id))
    #         # Probá primero SF, si no, por nombre
    #         state = self._first('res.country.state', dom + [('code', 'in', ['SF', 'S'])])
    #         if not state:
    #             state = self._first('res.country.state', dom + [('name', 'ilike', 'Santa Fe')])
    #         if not state and country:
    #             state = self._first('res.country.state', [('country_id', '=', country.id)])
    #         if not state:
    #             state = self._first('res.country.state', [('id', '!=', False)])

    #     # 3) Responsabilidad AFIP (si el campo existe)
    #     afip_resp = None
    #     if 'l10n_ar_afip_responsibility_type_id' in Partner._fields:
    #         # Preferir la de la compañía
    #         afip_resp = company.l10n_ar_afip_responsibility_type_id
    #         if not afip_resp:
    #             afip_resp = self._first('afip.responsibility.type', [('name', 'ilike', 'Consumidor Final')])
    #         if not afip_resp:
    #             afip_resp = self._first('afip.responsibility.type', [('id', '!=', False)])

    #     # 4) Tipo de identificación (si el campo existe)
    #     id_type = None
    #     if 'l10n_latam_identification_type_id' in Partner._fields:
    #         # Buscar DNI por nombre (sin xmlid)
    #         id_type = self._first('l10n_latam.identification.type', [('name', 'ilike', 'DNI')])
    #         if not id_type:
    #             id_type = self._first('l10n_latam.identification.type', [('id', '!=', False)])

    #     # import pdb; pdb.set_trace()
    #     # 5) Defaults mínimos (ojo: si NO querés pedir facturación, podés dejar varios en blanco)
    #     defaults = {
    #         'name': _('Guestdasasdas Buyer'),
    #         'company_name': _('Guestdsaasdasd Buyer'),
    #         'country_id': country.id if country else False,
    #         'state_id': state.id if state else False,
    #         # Estos son opcionales: ponelos solo si tu flujo realmente los necesita
    #         'phone': '2477502620',
    #         'street': 'Calle falsa 123456789999999',
    #         'city': 'Rosario??',
    #         'zip': '200122',
    #         'vat': '430265222289',
    #     }
    #     _logger.info("Paso por fotoapplygues y envio: %s", defaults)
               
    #     if afip_resp:
    #         defaults['l10n_ar_afip_responsibility_type_id'] = afip_resp.id
    #     if id_type:
    #         defaults['l10n_latam_identification_type_id'] = id_type.id

    #     # Aplicar solo si el field existe y si no vino ya en address_values
    #     for field, value in defaults.items():
    #         if field in Partner._fields:
    #             address_values.setdefault(field, value)

    def _fotoapp_validate_single_photographer(self, order_sudo):
        photo_lines = order_sudo.order_line.filtered(lambda l: l.foto_photographer_id)
        photographers = set(photo_lines.mapped('foto_photographer_id').ids)
        if len(photographers) > 1:
            request.session['website_sale_cart_warning'] = _(
                'No está permitido agregar fotos de varios fotógrafos al carrito. Separá los carritos por favor.'
            )
            return request.redirect('/shop/cart')
        return None


    ## _validate_address_values es el método que valida los datos de dirección en checkout, y es el que vamos a sobreescribir
    ## para no pedir datos de dirección en el guest checkout de FotoApp (y setear valores por defecto)
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
        
        _logger.info("LOG LOG LOG ----FotoApp Guest Checkout - Address Values before validation: %s", address_values)

        order_sudo = request.website.sale_get_order()
        is_guest = self._fotoapp_is_guest_checkout(order_sudo)

        if is_guest:
            # Defaults mínimos que sí querés guardar
            address_values.setdefault('name', _('Guestssssssssssssss Buyer'))
            address_values.setdefault('company_name', _('Guest Buyerssssssssssssss'))
            country_ar = self._first('res.country', [('code', '=', 'AR')])
            country_id = country_ar.id if country_ar else (request.website.company_id.country_id.id or False)
            address_values.setdefault('country_id', country_id)

            state = None
            if country_id:
                state = self._first('res.country.state', [('country_id', '=', country_id), ('code', 'in', ['S', 'SF'])])
                if not state:
                    state = self._first('res.country.state', [('country_id', '=', country_id), ('name', 'ilike', 'Santa Fe')])
                if not state:
                    state = self._first('res.country.state', [('country_id', '=', country_id)])
            if not state:
                state = self._first('res.country.state', [('id', '!=', False)])
            address_values.setdefault('state_id', state.id if state else False)

            address_values.setdefault('city', 'Rosario')
            address_values.setdefault('zip', '2000')
            address_values.setdefault('phone', '2477610100')
            address_values.setdefault('vat', '43026589')
            address_values.setdefault('street', 'Calle falsa 123')
            address_values.setdefault('street2', '4-1')
            
            _logger.info("FotoApp Guest Checkout - Address Values previews AFIP: %s", address_values)

            Partner = request.env['res.partner']
            if 'l10n_ar_afip_responsibility_type_id' in Partner._fields:
                afip_cf = self._first('afip.responsibility.type', [('name', 'ilike', 'Consumidor Final')])
                if afip_cf:
                    address_values.setdefault('l10n_ar_afip_responsibility_type_id', afip_cf.id)

            if 'l10n_latam_identification_type_id' in Partner._fields:
                dni_type = self._first('l10n_latam.identification.type', [('name', 'ilike', 'DNI')])
                if dni_type:
                    address_values.setdefault('l10n_latam_identification_type_id', dni_type.id)

            _logger.info("FotoApp Guest Checkout - Address Values after defaults: %s", address_values)


            # self._fotoapp_apply_guest_defaults(address_values, order_sudo)
            
            email = (address_values.get('email') or '').strip()
            if not email or not EMAIL_RE.match(email):
                return set(), {'email'}, [_('Ingresá un correo válido.')]
            required_fields = ['email']

            return set(), set(), []

        # flujo normal (logueado)
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
