# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FotoappPlan(models.Model):
    _name = 'fotoapp.plan'
    _description = 'Planes de suscripción FotoApp'
    _order = 'sequence, monthly_fee desc, id'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True, copy=False)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(string='Descripción interna')
    website_description = fields.Html(string='Descripción para la web')
    billing_interval = fields.Selection([
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
    ], string='Intervalo de facturación', default='monthly')
    monthly_fee = fields.Monetary(string='Precio mensual', required=True)
    yearly_fee = fields.Monetary(string='Precio anual')
    setup_fee = fields.Monetary(string='Cargo inicial')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.company.currency_id.id
    )
    photo_limit = fields.Integer(string='Límite de fotos', help='0 significa ilimitado.')
    album_limit = fields.Integer(string='Límite de álbumes', help='0 significa ilimitado.')
    event_limit = fields.Integer(string='Límite de eventos', help='0 significa ilimitado.')
    storage_limit_gb = fields.Float(string='[Deprecated] Límite almacen (GB)', help='Usar storage_limit_mb', default=0.0)
    storage_limit_mb = fields.Integer(string='Límite de almacenamiento (MB)', help='0 significa ilimitado.')
    featured_event_limit = fields.Integer(string='Eventos destacados incluidos')
    download_bundle_limit = fields.Integer(string='Descargas full-res incluidas', help='0 significa ilimitado.')
    autopublish_enabled = fields.Boolean(string='Autopublicación disponible', default=True)
    proofing_enabled = fields.Boolean(string='Herramientas de proofing', default=True)
    private_gallery_enabled = fields.Boolean(string='Galería privada', default=True)
    advanced_watermark_enabled = fields.Boolean(string='Marca de agua avanzada', default=True)
    api_access_enabled = fields.Boolean(string='API / Integraciones', default=False)
    commission_percent = fields.Float(string='Comisión estándar (%)', default=22.0)
    transaction_fee_percent = fields.Float(string='Fee por transacción (%)', default=3.0)
    payout_delay_days = fields.Integer(string='Días de espera para pago', default=7)
    mercadopago_plan_code = fields.Char(string='Código plan Mercado Pago')
    notes = fields.Text(string='Notas internas')
    subscription_ids = fields.One2many('fotoapp.plan.subscription', 'plan_id', string='Suscripciones')
    subscription_count = fields.Integer(string='Suscripciones activas', compute='_compute_subscription_count')
    product_template_id = fields.Many2one('product.template', string='Producto asociado', copy=False)
    product_variant_id = fields.Many2one('product.product', string='Variante ecommerce', copy=False)

    _sql_constraints = [
        ('plan_code_unique', 'unique(code)', 'El código del plan debe ser único.'),
    ]

    @api.depends('subscription_ids.state')
    def _compute_subscription_count(self):
        active_states = {'trial', 'active', 'grace'}
        for plan in self:
            plan.subscription_count = len(plan.subscription_ids.filtered(lambda sub: sub.state in active_states))

    @api.constrains('commission_percent', 'transaction_fee_percent')
    def _check_percentages(self):
        for plan in self:
            if plan.commission_percent < 0 or plan.transaction_fee_percent < 0:
                raise ValidationError(_('Los porcentajes no pueden ser negativos.'))
            if plan.commission_percent > 100 or plan.transaction_fee_percent > 100:
                raise ValidationError(_('Los porcentajes no pueden superar 100%.'))

    @api.constrains('photo_limit', 'album_limit', 'event_limit', 'storage_limit_gb')
    def _check_positive_limits(self):
        for plan in self:
            numeric_limits = [plan.photo_limit, plan.album_limit, plan.event_limit]
            if any(limit < 0 for limit in numeric_limits if limit is not None):
                raise ValidationError(_('Los límites no pueden ser negativos.'))
            if plan.storage_limit_gb and plan.storage_limit_gb < 0:
                raise ValidationError(_('El almacenamiento no puede ser negativo.'))

    def get_limit_payload(self):
        self.ensure_one()
        return {
            'photo': self.photo_limit,
            'album': self.album_limit,
            'event': self.event_limit,
            'storage_mb': self.storage_limit_mb or int((self.storage_limit_gb or 0.0) * 1024),
            'featured': self.featured_event_limit,
            'download_bundle': self.download_bundle_limit,
        }

    @api.model_create_multi
    def create(self, vals_list):
        plans = super().create(vals_list)
        plans._ensure_plan_products()
        return plans

    def write(self, vals):
        res = super().write(vals)
        self._ensure_plan_products()
        return res

    def _ensure_plan_products(self):
        for plan in self:
            plan._sync_plan_product()

    def _sync_plan_product(self):
        self.ensure_one()
        ProductTemplate = self.env['product.template'].sudo()
        product_vals = self._prepare_plan_product_vals()
        if not self.product_template_id: # Crear el producto si no existe
            template = ProductTemplate.create(product_vals)
            self.product_template_id = template.id
            self.product_variant_id = template.product_variant_id.id
            template.fotoapp_plan_id = self.id
        else: # Actualizar el producto existente
            self.product_template_id.write(product_vals)
            if self.product_variant_id:
                self.product_variant_id.write({'list_price': self.monthly_fee})
            self.product_template_id.fotoapp_plan_id = self.id

    def _prepare_plan_product_vals(self):
        self.ensure_one()
        ProductTemplate = self.env['product.template']
        vals = {
            'name': self.name,
            'sale_ok': True, #sirve para vender el producto en el ecommerce
            'purchase_ok': False, 
            'invoice_policy': 'order', #facturar al hacer el pedido
            'list_price': self.monthly_fee,
            'description_sale': _('%s · Plan mensual para fotógrafos') % self.name,
            'fotoapp_plan_id': self.id,
            'website_published': True,
        }
        if 'detailed_type' in ProductTemplate._fields:
            vals['detailed_type'] = 'service'
        else:
            vals['type'] = 'service'
        return vals
