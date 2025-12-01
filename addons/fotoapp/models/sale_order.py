from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order._process_fotoapp_plan_lines()
        return res

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
                next_date = fields.Date.add(self.date_order.date(), months=1) if self.date_order else fields.Date.add(fields.Date.context_today(self), months=1)
                subscription.write({
                    'state': 'active',
                    'next_billing_date': next_date,
                })
                continue
            if subscription:
                subscription.action_cancel()
            partner._activate_photo_plan(plan, order=self)
