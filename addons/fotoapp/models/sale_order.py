from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    fotoapp_photographer_id = fields.Many2one('res.partner', string='Fotógrafo (FotoApp)', copy=False)
    fotoapp_plan_id = fields.Many2one('fotoapp.plan', string='Plan vigente', copy=False)
    fotoapp_commission_percent = fields.Float(string='Comisión del plan (%)', copy=False)
    fotoapp_platform_commission_amount = fields.Monetary(string='Comisión plataforma', currency_field='currency_id', copy=False)
    fotoapp_photographer_amount = fields.Monetary(string='Monto para fotógrafo', currency_field='currency_id', copy=False)

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order._process_fotoapp_plan_lines()
            order._process_fotoapp_debt_payments()
        return res

    def _prepare_payment_transaction_vals(self, **kwargs):
        self._ensure_single_photographer_orders()
        vals = super()._prepare_payment_transaction_vals(**kwargs)
        if len(self) == 1 and self.fotoapp_photographer_id:
            vals.update({
                'fotoapp_photographer_id': self.fotoapp_photographer_id.id,
                'fotoapp_plan_id': self.fotoapp_plan_id.id if self.fotoapp_plan_id else False,
                'fotoapp_commission_percent': self.fotoapp_commission_percent,
                'fotoapp_platform_commission_amount': self.fotoapp_platform_commission_amount,
                'fotoapp_photographer_amount': self.fotoapp_photographer_amount,
            })
        return vals

    def _process_fotoapp_plan_lines(self):
        PlanSubscription = self.env['fotoapp.plan.subscription']
        active_states = {'draft', 'trial', 'active', 'grace'}
        for line in self.order_line:
            plan = line.product_id.product_tmpl_id.fotoapp_plan_id
            if not plan:
                continue
            partner = self.partner_id.commercial_partner_id
            subscription = PlanSubscription.search([
                ('partner_id', '=', partner.id),
                ('state', 'in', list(active_states)),
            ], limit=1)
            if subscription and subscription.plan_id == plan:
                base_date = self.date_order.date() if self.date_order else fields.Date.context_today(self)
                next_date = fields.Date.add(base_date, days=30)
                subscription.write({
                    'state': 'active',
                    'next_billing_date': next_date,
                })
                continue
            if subscription:
                subscription.action_cancel()
            partner._activate_photo_plan(plan, order=self)

    def _process_fotoapp_debt_payments(self):
        Debt = self.env['fotoapp.debt']
        debts = Debt.search([
            ('sale_order_id', '=', self.id),
            ('state', 'in', ['pending', 'in_grace'])
        ])
        if debts:
            debts.mark_paid(paid_date=fields.Datetime.now())

    def _ensure_single_photographer_orders(self):
        for order in self:
            if order.state not in ('draft', 'sent'):
                continue
            photo_lines = order.order_line.filtered(lambda l: l.foto_photographer_id)
            if not photo_lines:
                order._apply_photographer_metadata(order.partner_id.active_plan_subscription_id)
                continue
            photographers = photo_lines.mapped('foto_photographer_id')
            for idx, photographer in enumerate(photographers):
                target_order = order if idx == 0 else order._duplicate_for_photographer()
                if idx > 0:
                    lines = photo_lines.filtered(lambda l, p=photographer: l.foto_photographer_id == p)
                    lines.write({'order_id': target_order.id})
                target_order._apply_photographer_metadata(
                    photographer.active_plan_subscription_id,
                    photographer=photographer,
                )
                target_order._recompute_fotoapp_commission()
            if not photographers:
                order._recompute_fotoapp_commission()

    def _duplicate_for_photographer(self):
        self.ensure_one()
        duplicate = self.copy()
        duplicate.order_line.unlink()
        return duplicate

    def _apply_photographer_metadata(self, subscription, photographer=None):
        self.ensure_one()
        photographer = photographer or (subscription.partner_id if subscription else self.partner_id.commercial_partner_id)
        plan = subscription.plan_id if subscription else (photographer.plan_id if photographer else False)
        commission = plan.commission_percent if plan and plan.commission_percent else 0.0
        self.write({
            'fotoapp_photographer_id': photographer.id if photographer else False,
            'fotoapp_plan_id': plan.id if plan else False,
            'fotoapp_commission_percent': commission,
        })

    def _recompute_fotoapp_commission(self):
        for order in self:
            percent = (order.fotoapp_commission_percent or 0.0) / 100.0
            platform_amount = (order.amount_total or 0.0) * percent
            photographer_amount = (order.amount_total or 0.0) - platform_amount
            order.write({
                'fotoapp_platform_commission_amount': platform_amount,
                'fotoapp_photographer_amount': photographer_amount,
            })
