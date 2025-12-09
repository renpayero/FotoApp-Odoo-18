# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


FREEMIUM_CODE = 'FREEMIUM'


class FotoappPlanSubscription(models.Model):
    _name = 'fotoapp.plan.subscription'
    _description = 'Suscripciones de planes para fotógrafos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'state desc, activation_date desc, id desc'

    name = fields.Char(string='Referencia', required=True, copy=False, default=lambda self: self._default_name())
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Fotógrafo',
        required=True,
        domain="[('is_photographer', '=', True)]",
        tracking=True
    )
    plan_id = fields.Many2one('fotoapp.plan', string='Plan', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('trial', 'Periodo de prueba'), # Estado durante el periodo de prueba
        ('active', 'Activa'),
        ('grace', 'En gracia'), # Estado en periodo de gracia después de la expiración
        ('suspended', 'Suspendida'),
        ('expired', 'Expirada'),
        ('canceled', 'Cancelada'),
    ], string='Estado', default='draft', tracking=True)
    start_date = fields.Date(string='Fecha de registro', default=fields.Date.context_today)
    activation_date = fields.Date(string='Fecha de activación')
    trial_end_date = fields.Date(string='Fin de prueba')
    next_billing_date = fields.Date(string='Próxima facturación')
    end_date = fields.Date(string='Fin de vigencia')
    grace_until = fields.Date(string='Gracia hasta')
    cancellation_date = fields.Date(string='Fecha de cancelación')
    autopay_enabled = fields.Boolean(string='Cobros automáticos', default=True)
    mercadopago_preapproval_id = fields.Char(string='Preapproval Mercado Pago')
    mercadopago_status = fields.Char(string='Estado Mercado Pago')
    mercadopago_checkout_url = fields.Char(string='URL renovación MP')
    notes = fields.Text(string='Notas internas')
    plan_photo_limit = fields.Integer(string='Límite de fotos', related='plan_id.photo_limit', store=False)
    plan_album_limit = fields.Integer(string='Límite de álbumes', related='plan_id.album_limit', store=False)
    plan_event_limit = fields.Integer(string='Límite de eventos', related='plan_id.event_limit', store=False)
    plan_storage_limit_gb = fields.Float(string='Límite de almacenamiento (GB)', related='plan_id.storage_limit_gb', store=False)
    plan_storage_limit_mb = fields.Integer(string='Límite de almacenamiento (MB)', related='plan_id.storage_limit_mb', store=False)
    usage_photo_count = fields.Integer(compute='_compute_usage_metrics', store=True)
    usage_album_count = fields.Integer(compute='_compute_usage_metrics', store=True)
    usage_event_count = fields.Integer(compute='_compute_usage_metrics', store=True)
    usage_storage_bytes = fields.Integer(compute='_compute_usage_metrics', store=True)
    usage_storage_mb = fields.Float(string='Uso de almacenamiento (MB)', compute='_compute_usage_metrics', store=True)
    storage_limit_bytes = fields.Integer(string='Límite de almacenamiento (bytes)', compute='_compute_limit_flags', store=True)
    usage_last_update = fields.Datetime(string='Última actualización', readonly=True)
    is_over_photo_limit = fields.Boolean(compute='_compute_limit_flags', store=True)
    is_over_album_limit = fields.Boolean(compute='_compute_limit_flags', store=True)
    is_over_event_limit = fields.Boolean(compute='_compute_limit_flags', store=True)
    is_over_storage_limit = fields.Boolean(compute='_compute_limit_flags', store=True)
    event_ids = fields.One2many('tienda.foto.evento', 'plan_subscription_id', string='Eventos')
    album_ids = fields.One2many('tienda.foto.album', 'plan_subscription_id', string='Álbumes')
    asset_ids = fields.One2many('tienda.foto.asset', 'plan_subscription_id', string='Fotos')
    responsible_user_id = fields.Many2one('res.users', string='Ejecutivo asignado', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id)

    @api.depends('asset_ids', 'asset_ids.file_size_bytes', 'album_ids', 'event_ids')
    #esta funcion calcula los usos actuales de la suscripcion, como la cantidad de fotos, albumes, eventos y almacenamiento usado
    def _compute_usage_metrics(self):
        for subscription in self:
            subscription.usage_photo_count = len(subscription.asset_ids)
            subscription.usage_album_count = len(subscription.album_ids)
            subscription.usage_event_count = len(subscription.event_ids)
            bytes_used = sum(subscription.asset_ids.mapped('file_size_bytes')) if subscription.asset_ids else 0
            subscription.usage_storage_bytes = bytes_used
            subscription.usage_storage_mb = bytes_used / (1024 ** 2) if bytes_used else 0.0
            subscription.usage_last_update = fields.Datetime.now()

    @api.depends('usage_photo_count', 'usage_album_count', 'usage_event_count', 'usage_storage_bytes')
    #esta funcion calcula si se han superado los limites del plan
    def _compute_limit_flags(self):
        for subscription in self:
            plan = subscription.plan_id
            subscription.is_over_photo_limit = bool(plan.photo_limit and subscription.usage_photo_count > plan.photo_limit)
            subscription.is_over_album_limit = bool(plan.album_limit and subscription.usage_album_count > plan.album_limit)
            subscription.is_over_event_limit = bool(plan.event_limit and subscription.usage_event_count > plan.event_limit)
            storage_limit_mb = plan.storage_limit_mb or int((plan.storage_limit_gb or 0.0) * 1024)
            storage_limit_bytes = (storage_limit_mb or 0) * 1024 * 1024
            subscription.storage_limit_bytes = int(storage_limit_bytes)
            subscription.is_over_storage_limit = bool(storage_limit_bytes and subscription.usage_storage_bytes > storage_limit_bytes)

    def action_activate(self):
        for subscription in self:
            if subscription.state not in {'draft', 'trial', 'grace'}:
                continue
            subscription.state = 'active'
            subscription.activation_date = fields.Date.context_today(subscription)
            if not subscription.next_billing_date:
                subscription.next_billing_date = fields.Date.add(subscription.activation_date, days=30)

    def action_enter_grace(self):
        for subscription in self:
            subscription.state = 'grace'
            subscription.grace_until = subscription.grace_until or fields.Date.add(fields.Date.context_today(subscription), days=7)

    def action_suspend(self):
        for subscription in self:
            subscription.state = 'suspended'

    def action_cancel(self):
        for subscription in self:
            subscription.state = 'canceled'
            subscription.cancellation_date = fields.Date.context_today(subscription)

    def action_mark_expired(self):
        for subscription in self:
            subscription.state = 'expired'
            subscription.end_date = fields.Date.context_today(subscription)

    def check_limits(self, metric):
        self.ensure_one()
        plan = self.plan_id
        if metric == 'photo' and plan.photo_limit:
            return self.usage_photo_count <= plan.photo_limit
        if metric == 'album' and plan.album_limit:
            return self.usage_album_count <= plan.album_limit
        if metric == 'event' and plan.event_limit:
            return self.usage_event_count <= plan.event_limit
        if metric == 'storage':
            limit_bytes = (plan.storage_limit_mb or int((plan.storage_limit_gb or 0.0) * 1024)) * 1024 * 1024
            if limit_bytes:
                return self.usage_storage_bytes <= limit_bytes
            return True
        return True

    def name_get(self):
        return [(sub.id, f"{sub.name} ({sub.plan_id.name})") for sub in self]

    @api.constrains('partner_id', 'plan_id', 'state')
    def _constrain_unique_active(self):
        active_states = {'trial', 'active', 'grace'}
        for sub in self.filtered(lambda s: s.state in active_states):
            domain = [
                ('id', '!=', sub.id),
                ('partner_id', '=', sub.partner_id.id),
                ('state', 'in', list(active_states)),
            ]
            if self.search_count(domain):
                raise ValidationError(_('El fotógrafo ya posee una suscripción activa.'))

    @api.model
    def _default_name(self):
        return self.env['ir.sequence'].next_by_code('fotoapp.plan.subscription') or _('Suscripción sin código')

    def can_store_bytes(self, bytes_to_add):
        self.ensure_one()
        limit_mb = self.plan_id.storage_limit_mb or int((self.plan_id.storage_limit_gb or 0.0) * 1024)
        if not limit_mb:
            return True
        limit_bytes = limit_mb * 1024 * 1024
        return (self.usage_storage_bytes + bytes_to_add) <= limit_bytes

    def remaining_storage_bytes(self):
        self.ensure_one()
        limit_mb = self.plan_id.storage_limit_mb or int((self.plan_id.storage_limit_gb or 0.0) * 1024)
        if not limit_mb:
            return False
        limit_bytes = limit_mb * 1024 * 1024
        return max(limit_bytes - self.usage_storage_bytes, 0)

    # ------------------------------------------------------------------
    # Gestión de deudas y renovación
    # ------------------------------------------------------------------

    def _handle_successful_payment(self):
        for subscription in self:
            subscription.write({
                'state': 'active',
                'grace_until': False,
            })

    def _apply_nonpayment_downgrade(self):
        Plan = self.env['fotoapp.plan']
        freemium_plan = Plan.search([('code', '=', FREEMIUM_CODE)], limit=1)
        for subscription in self:
            values = {
                'state': 'active',
                'next_billing_date': False,
            }
            if freemium_plan and subscription.plan_id != freemium_plan:
                values['plan_id'] = freemium_plan.id
            subscription.write(values)

    @api.model
    def _cron_generate_subscription_debts(self):
        today = fields.Date.context_today(self)
        Debt = self.env['fotoapp.debt'].sudo()
        domain = [
            ('state', 'in', ['trial', 'active', 'grace']),
            ('plan_id.code', '!=', FREEMIUM_CODE),
            ('next_billing_date', '!=', False),
        ]
        subscriptions = self.sudo().search(domain)
        for subscription in subscriptions:
            billing_date = subscription.next_billing_date or today
            existing = Debt.search([
                ('subscription_id', '=', subscription.id),
                ('debt_type', '=', 'subscription'),
                ('billing_date', '=', billing_date),
            ], limit=1)
            next_cycle_date = fields.Date.add(billing_date, days=30)
            if existing:
                subscription.sudo().write({'next_billing_date': next_cycle_date})
                continue
            amount = subscription.plan_id.monthly_fee
            if not amount:
                subscription.sudo().write({'next_billing_date': next_cycle_date})
                continue
            debt_vals = {
                'partner_id': subscription.partner_id.id,
                'subscription_id': subscription.id,
                'plan_id': subscription.plan_id.id,
                'debt_type': 'subscription',
                'amount': amount,
                'currency_id': subscription.plan_id.currency_id.id,
                'billing_date': billing_date,
                'due_date': billing_date,
                'grace_end_date': fields.Date.add(billing_date, days=15),
            }
            Debt.create(debt_vals)
            subscription.sudo().write({'next_billing_date': next_cycle_date})

    @api.model
    def _cron_handle_overdue_debts(self):
        today = fields.Date.context_today(self)
        Debt = self.env['fotoapp.debt'].sudo()
        pending = Debt.search([
            ('debt_type', '=', 'subscription'),
            ('state', '=', 'pending'),
            ('due_date', '<', today),
        ])
        pending.mark_in_grace()

        expired = Debt.search([
            ('debt_type', '=', 'subscription'),
            ('state', 'in', ['pending', 'in_grace']),
            ('grace_end_date', '<', today),
        ])
        expired.mark_expired()
