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
    fotoapp_mp_gateway_journal_id = fields.Many2one(
        'account.journal',
        string='Diario de pagos Mercado Pago',
        domain="[('type', 'in', ('bank', 'cash'))]",
        config_parameter='fotoapp.mp_gateway_journal_id',
        help='Diario bancario que se usará para registrar automáticamente los cobros de Mercado Pago.'
    )
    fotoapp_afip_environment = fields.Selection(
        [('testing', 'Homologación / Testing'), ('production', 'Producción')],
        string='Modo AFIP',
        default='testing',
        config_parameter='fotoapp.afip_environment'
    )
    fotoapp_afip_pos_number = fields.Char(
        string='Punto de venta AFIP',
        config_parameter='fotoapp.afip_pos_number'
    )
    fotoapp_afip_certificate_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Certificado AFIP (PEM)',
        config_parameter='fotoapp.afip_certificate_attachment_id',
        help='Adjuntá el archivo .pem del certificado emitido por AFIP.'
    )
    fotoapp_afip_private_key_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Clave privada AFIP (PEM)',
        config_parameter='fotoapp.afip_private_key_attachment_id',
        help='Adjuntá la clave privada asociada al certificado AFIP.'
    )
    fotoapp_afip_passphrase = fields.Char(
        string='Passphrase certificado',
        config_parameter='fotoapp.afip_passphrase'
    )
