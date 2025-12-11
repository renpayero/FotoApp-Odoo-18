# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fotoapp_mp_client_id = fields.Char(
        string='Mercado Pago Client ID',
        config_parameter='fotoapp.mp_client_id'
    )
    fotoapp_mp_client_secret = fields.Char(
        string='Mercado Pago Client Secret',
        config_parameter='fotoapp.mp_client_secret'
    )
    fotoapp_mp_redirect_uri = fields.Char(
        string='Redirect URI para OAuth',
        config_parameter='fotoapp.mp_redirect_uri',
        help='URL completa que Mercado Pago usará para devolver el código de autorización. '
             'Usa el dominio público de tu instancia y termina con /fotoapp/mercadopago/oauth/callback'
    )
