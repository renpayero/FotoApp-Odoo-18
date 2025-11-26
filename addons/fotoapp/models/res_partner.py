# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_photographer = fields.Boolean(string='Es fotógrafo', default=False, tracking=True)
    photographer_bio = fields.Text(string='Biografía corta')
    portfolio_url = fields.Char(string='URL de portafolio')
    photographer_code = fields.Char(string='Código público', copy=False)
    onboarding_stage = fields.Selection([
        ('lead', 'Lead'),
        ('invited', 'Invitado'),
        ('pending_setup', 'Pendiente de setup'),
        ('ready', 'Listo para vender'),
    ], string='Etapa de onboarding', default='lead', tracking=True)
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
    album_ids = fields.One2many(
        comodel_name='tienda.foto.album',
        inverse_name='photographer_id',
        string='Álbumes creados'
    )
    asset_ids = fields.One2many(
        comodel_name='tienda.foto.asset',
        inverse_name='photographer_id',
        string='Fotos subidas'
    )
    plan_subscription_ids = fields.One2many(
        comodel_name='fotoapp.plan.subscription',
        inverse_name='partner_id',
        string='Suscripciones'
    )
    active_plan_subscription_id = fields.Many2one(
        comodel_name='fotoapp.plan.subscription',
        compute='_compute_active_subscription',
        string='Suscripción vigente',
        store=True
    )
    plan_id = fields.Many2one(
        comodel_name='fotoapp.plan',
        compute='_compute_active_subscription',
        string='Plan vigente',
        store=True
    )
    event_count = fields.Integer(string='Eventos publicados', compute='_compute_metrics', store=True)
    album_count = fields.Integer(string='Álbumes', compute='_compute_metrics', store=True)
    asset_count = fields.Integer(string='Fotos', compute='_compute_metrics', store=True)
    total_storage_bytes = fields.Integer(string='Almacenamiento usado', compute='_compute_metrics', store=True)
    company_currency_id = fields.Many2one('res.currency', string='Moneda compañía', related='company_id.currency_id', store=True, readonly=True)
    gross_sales_total = fields.Monetary(string='Ventas generadas', currency_field='company_currency_id', compute='_compute_metrics', store=True)
    statement_ids = fields.One2many('fotoapp.photographer.statement', 'partner_id', string='Liquidaciones')
    payout_preference = fields.Selection([
        ('mercadopago', 'Mercado Pago'),
        ('bank_transfer', 'Transferencia bancaria'),
        ('cash', 'Pago manual'),
    ], string='Método de pago preferido', default='mercadopago')
    payout_account = fields.Char(string='Cuenta de pago / CBU / Alias')
    fotoapp_next_photo_identifier = fields.Integer(
        string='Próximo identificador de foto',
        default=0,
        copy=False,
        help='Mantiene la secuencia interna para numerar fotos automáticamente.'
    )

    def get_watermark_payload(self):
        self.ensure_one()
        return {
            'image': self.watermark_image,
            'opacity': min(max(self.watermark_opacity, 0), 100),
            'scale': min(max(self.watermark_scale, 0.05), 1.0),
        }

    @api.depends('plan_subscription_ids.state', 'plan_subscription_ids.plan_id')
    def _compute_active_subscription(self):
        active_states = {'trial', 'active', 'grace'}
        for partner in self:
            active_sub = partner.plan_subscription_ids.filtered(lambda sub: sub.state in active_states)[:1]
            partner.active_plan_subscription_id = active_sub.id if active_sub else False
            partner.plan_id = active_sub.plan_id.id if active_sub else False

    @api.depends('foto_event_ids', 'album_ids', 'asset_ids', 'asset_ids.file_size_bytes', 'asset_ids.sale_total_amount')
    def _compute_metrics(self):
        for partner in self:
            partner.event_count = len(partner.foto_event_ids)
            partner.album_count = len(partner.album_ids)
            partner.asset_count = len(partner.asset_ids)
            partner.total_storage_bytes = sum(partner.asset_ids.mapped('file_size_bytes'))
            partner.gross_sales_total = sum(partner.asset_ids.mapped('sale_total_amount'))

    def write(self, vals):
        watermark_fields = {'watermark_image', 'watermark_opacity', 'watermark_scale'}
        should_regenerate = bool(watermark_fields.intersection(vals.keys()))
        result = super().write(vals)
        if should_regenerate:
            self._regenerate_published_assets_watermark()
        return result

    def _regenerate_published_assets_watermark(self):
        Asset = self.env['tienda.foto.asset'].sudo()
        for partner in self:
            assets = Asset.search([
                ('photographer_id', '=', partner.id),
                ('lifecycle_state', '=', 'published'),
            ])
            if assets:
                assets.regenerate_watermark()
