import secrets
from dateutil.relativedelta import relativedelta
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    fotoapp_photographer_id = fields.Many2one('res.partner', string='Fotógrafo (FotoApp)', copy=False)
    fotoapp_plan_id = fields.Many2one('fotoapp.plan', string='Plan vigente', copy=False)
    fotoapp_commission_percent = fields.Float(string='Comisión del plan (%)', copy=False)
    fotoapp_platform_commission_amount = fields.Monetary(string='Comisión plataforma', currency_field='currency_id', copy=False)
    fotoapp_photographer_amount = fields.Monetary(string='Monto para fotógrafo', currency_field='currency_id', copy=False)
    download_token = fields.Char(string='Token descarga FotoApp', copy=False)
    download_token_expires_at = fields.Datetime(string='Expira link descarga', copy=False)
    download_email_sent = fields.Boolean(string='Email descarga enviado', default=False, copy=False)

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order._process_fotoapp_plan_lines()
            order._process_fotoapp_debt_payments()
            order._refresh_photo_publication_clock()
        return res

    def _prepare_payment_transaction_vals(self, **kwargs):
        self._ensure_single_photographer_orders()
        if len(self) == 1 and not self.fotoapp_photographer_id:
            photographer = self._fotoapp_detect_single_photographer()
            if photographer:
                self.sudo()._apply_photographer_metadata(
                    photographer.active_plan_subscription_id,
                    photographer=photographer,
                )
                self.sudo()._recompute_fotoapp_commission()
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
        PlanSubscription = self.env['sale.subscription']
        active_states = {'draft', 'trial', 'active', 'grace'}
        for line in self.order_line:
            plan = line.product_id.product_tmpl_id.fotoapp_plan_id
            if not plan:
                continue
            partner = self.partner_id.commercial_partner_id
            subscription = PlanSubscription.search([
                ('partner_id', '=', partner.id),
                ('fotoapp_is_photographer_plan', '=', True),
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
            mp_transactions = self.transaction_ids.filtered(lambda tx: tx.provider_code == 'mercado_pago' and tx.state == 'done')
            if mp_transactions:
                debts._fotoapp_register_gateway_payment(transaction=mp_transactions[:1])

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

    def _refresh_photo_publication_clock(self):
        assets = self.mapped('order_line.foto_asset_id')
        if assets:
            assets.sudo()._bump_publication_clock()

    def _fotoapp_detect_single_photographer(self):
        self.ensure_one()
        photo_lines = self.order_line.filtered(lambda line: line.foto_photographer_id)
        if not photo_lines:
            return False
        photographer_ids = set(photo_lines.mapped('foto_photographer_id').ids)
        if len(photographer_ids) > 1:
            raise ValidationError(_(
                'El carrito contiene fotos de distintos fotógrafos. Completa o vacía esa compra antes de '
                'continuar.'
            ))
        return photo_lines[:1].foto_photographer_id

    def _fotoapp_ensure_download_token(self, validity_days=30):
        for order in self:
            if order.download_token and order.download_token_expires_at and order.download_token_expires_at > fields.Datetime.now():
                continue
            token = secrets.token_urlsafe(32)
            expires_at = fields.Datetime.now() + relativedelta(days=validity_days)
            order.write({
                'download_token': token,
                'download_token_expires_at': expires_at,
                'download_email_sent': False,
            })
        return True

    def _fotoapp_send_download_email(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        ICP = self.env['ir.config_parameter'].sudo()
        default_from = ICP.get_param('mail.default.from')
        fallback_from = self.env.company.email or self.env.user.email_formatted or default_from
        for order in self:
            if not order.partner_id.email:
                continue
            order._fotoapp_ensure_download_token()
            if order.download_email_sent:
                continue
            link = f"{base_url}/fotoapp/public_download/{order.download_token}"
            body = _(
                "Hola,<br/>Tu pago fue confirmado. Descargá tus fotos desde este enlace (válido 30 días): "
                "<a href='%(link)s'>%(link)s</a>",
                link=link,
            )
            mail_values = {
                'subject': _('Tus fotos están listas'),
                'body_html': body,
                'email_to': order.partner_id.email,
                'author_id': self.env.user.partner_id.id,
                'email_from': default_from or fallback_from,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()
            order.write({'download_email_sent': True})
        return True
