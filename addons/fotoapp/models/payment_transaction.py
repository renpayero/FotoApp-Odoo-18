# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round

from odoo.addons.payment_mercado_pago import const


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    fotoapp_photographer_id = fields.Many2one('res.partner', string='Fotógrafo (FotoApp)', copy=False)
    fotoapp_plan_id = fields.Many2one('fotoapp.plan', string='Plan FotoApp', copy=False)
    fotoapp_commission_percent = fields.Float(string='Comisión plan (%)', copy=False)
    fotoapp_platform_commission_amount = fields.Monetary(
        string='Comisión plataforma', currency_field='currency_id', copy=False
    )
    fotoapp_photographer_amount = fields.Monetary(
        string='Monto destinado al fotógrafo', currency_field='currency_id', copy=False
    )

    def _send_api_request(self, method, endpoint, *, params=None, data=None, json=None, **kwargs):
        self.ensure_one()
        if self.provider_code == 'mercado_pago' and self.fotoapp_photographer_id:
            kwargs.setdefault('seller_access_token', self._fotoapp_get_seller_token())
        return super()._send_api_request(
            method,
            endpoint,
            params=params,
            data=data,
            json=json,
            **kwargs,
        )

    def _mercado_pago_prepare_preference_request_payload(self):
        payload = super()._mercado_pago_prepare_preference_request_payload()
        if self.fotoapp_platform_commission_amount:
            payload['marketplace_fee'] = self._fotoapp_convert_amount(self.fotoapp_platform_commission_amount)
        metadata = payload.setdefault('metadata', {})
        metadata.update({
            'fotoapp_photographer_id': self.fotoapp_photographer_id.id if self.fotoapp_photographer_id else False,
            'fotoapp_commission_percent': self.fotoapp_commission_percent,
            'fotoapp_sale_orders': ','.join(self.sale_order_ids.mapped('name')),
        })
        return payload

    def _fotoapp_get_seller_token(self):
        self.ensure_one()
        partner = self.fotoapp_photographer_id.sudo()
        if not partner:
            raise ValidationError(_('No se pudo identificar el fotógrafo asociado al pedido.'))
        partner._mp_refresh_token_if_needed()
        access_token = partner.mp_access_token
        if not access_token:
            raise ValidationError(_(
                'El fotógrafo %(name)s debe conectar su cuenta de Mercado Pago antes de cobrar.',
                name=partner.display_name,
            ))
        if partner.mp_account_status != 'connected':
            raise ValidationError(_(
                'La cuenta de Mercado Pago de %(name)s no está lista (estado: %(status)s).',
                name=partner.display_name,
                status=dict(partner._fields['mp_account_status'].selection).get(partner.mp_account_status, partner.mp_account_status),
            ))
        return access_token

    def _fotoapp_convert_amount(self, amount):
        currency_code = self.currency_id.name
        decimal_places = const.CURRENCY_DECIMALS.get(currency_code)
        if decimal_places is not None:
            return float_round(amount, precision_digits=decimal_places, rounding_method='DOWN')
        return amount
