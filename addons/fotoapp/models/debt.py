# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class FotoappDebt(models.Model):
    _name = 'fotoapp.debt'
    _description = 'Deudas del fotógrafo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date DESC, id DESC'

    name = fields.Char(string='Referencia', required=True, copy=False,
                       default=lambda self: self._default_name())
    partner_id = fields.Many2one('res.partner', string='Fotógrafo', required=True, index=True)
    subscription_id = fields.Many2one('fotoapp.plan.subscription', string='Suscripción', index=True)
    plan_id = fields.Many2one('fotoapp.plan', string='Plan asociado')
    debt_type = fields.Selection([
        ('subscription', 'Renovación de plan'),
        ('commission', 'Comisión'),
        ('other', 'Otro'),
    ], string='Tipo de deuda', default='subscription', required=True, index=True)
    amount = fields.Monetary(string='Importe', required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True,
                                  default=lambda self: self._default_currency())
    billing_date = fields.Date(string='Periodo facturado', required=True)
    due_date = fields.Date(string='Fecha de vencimiento', required=True)
    grace_end_date = fields.Date(string='Fin de gracia', required=True)
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_grace', 'En periodo de gracia'),
        ('paid', 'Pagada'),
        ('expired', 'Expirada'),
    ], string='Estado', default='pending', tracking=True, index=True)
    sale_order_id = fields.Many2one('sale.order', string='Pedido de pago', copy=False)
    sale_order_line_id = fields.Many2one('sale.order.line', string='Línea asociada', copy=False)
    paid_date = fields.Datetime(string='Fecha de pago', copy=False)
    company_id = fields.Many2one('res.company', string='Compañía', required=True,
                                 default=lambda self: self.env.company.id)
    notes = fields.Text(string='Notas internas')

    _sql_constraints = [
        ('fotoapp_debt_unique_cycle',
         'unique(subscription_id, debt_type, billing_date)',
         'Ya existe una deuda generada para este ciclo.'),
    ]

    def _default_name(self):
        return self.env['ir.sequence'].next_by_code('fotoapp.debt') or _('Deuda')

    def _default_currency(self):
        ars = self.env.ref('base.ARS', raise_if_not_found=False)
        if not ars:
            ars = self.env['res.currency'].search([('name', '=', 'ARS')], limit=1)
        if ars and not ars.active:
            ars.sudo().write({'active': True})
        return ars.id if ars else self.env.company.currency_id.id

    def mark_paid(self, paid_date=None):
        for debt in self.filtered(lambda d: d.state != 'paid'):
            date_done = paid_date or fields.Datetime.now()
            debt.write({
                'state': 'paid',
                'paid_date': date_done,
            })
            subscription = debt.subscription_id
            if subscription:
                subscription._handle_successful_payment()

    def mark_in_grace(self):
        self.filtered(lambda d: d.state == 'pending').write({'state': 'in_grace'})

    def mark_expired(self):
        for debt in self.filtered(lambda d: d.state in ('pending', 'in_grace')):
            debt.state = 'expired'
            subscription = debt.subscription_id
            if subscription:
                subscription._apply_nonpayment_downgrade()

    def can_be_paid(self):
        self.ensure_one()
        return self.state in ('pending', 'in_grace')

    def get_portal_label(self):
        self.ensure_one()
        if self.debt_type == 'subscription':
            return _('Renovación de plan')
        if self.debt_type == 'commission':
            return _('Comisión pendiente')
        return _('Deuda')
