# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_photographer = fields.Boolean(string='Es fotógrafo', default=False, tracking=True)
    photographer_bio = fields.Text(string='Biografía corta')
    portfolio_url = fields.Char(string='URL de portafolio')
    watermark_image = fields.Image(
        string='Marca de agua',
        max_width=1024,
        max_height=1024,
        attachment=True,
        help='Imagen que se aplicará como marca de agua a las fotos de este fotógrafo.'
    )
    watermark_opacity = fields.Integer(
        string='Opacidad de marca de agua',
        default=60,
        help='Opacidad expresada en porcentaje (0-100).'
    )
    watermark_scale = fields.Float(
        string='Escala de marca de agua',
        default=0.3,
        help='Escala relativa frente a la imagen final (0-1).'
    )
    foto_event_ids = fields.One2many(
        comodel_name='tienda.foto.evento',
        inverse_name='photographer_id',
        string='Eventos fotográficos'
    )

    def get_watermark_payload(self):
        self.ensure_one()
        return {
            'image': self.watermark_image,
            'opacity': min(max(self.watermark_opacity, 0), 100),
            'scale': min(max(self.watermark_scale, 0.05), 1.0),
        }
