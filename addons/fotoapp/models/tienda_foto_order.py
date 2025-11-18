from odoo import models, fields, api

# tienda.foto.order (Carrito/orden independiente)

# name, partner_id o email libre, state (draft, pending_payment, paid, delivered),
# asset_ids, totales, mercadopago_preference_id, checkout_url, download_token.
# Método action_mark_paid que dispara entrega y CRM.

class TiendaFotoOrder(models.Model):
    _name = 'tienda.foto.order'
    _description = 'Órdenes de fotos'

    name = fields.Char(string='Nombre de la Orden', required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente'
    )
    email_libre = fields.Char(string='Email Libre')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('pending_payment', 'Pendiente de Pago'),
        ('paid', 'Pagado'),
        ('delivered', 'Entregado')
    ], string='Estado', default='draft')
    asset_ids = fields.Many2many(
        comodel_name='tienda.foto.asset',
        string='Activos de Fotos'
    )
    total = fields.Float(string='Total', compute='_compute_total', store=True)
    mercadopago_preference_id = fields.Char(string='MercadoPago Preference ID')
    checkout_url = fields.Char(string='URL de Checkout')
    download_token = fields.Char(string='Token de Descarga', readonly=True)

    @api.depends('asset_ids')
    def _compute_total(self):
        for order in self:
            total_assets = sum(asset.precio for asset in order.asset_ids)
            order.total = total_assets
    def action_mark_paid(self):
        for order in self:
            order.state = 'paid'
            self.env['crm.lead'].create({
                'name': f'Orden de Foto {order.name} - {order.partner_id.name or order.email_libre}',
                'partner_id': order.partner_id.id,
                'description': f'Orden marcada como pagada. Total: {order.total}',
            })
            pass
        # Lógica para disparar la entrega de las fotos al cliente
        # (por ejemplo, enviar un email con enlaces de descarga)
        # Esta parte depende de cómo se gestione la entrega en tu sistema
        # Aquí solo se deja un comentario como placeholder
        # self._enviar_entrega_al_cliente(order)
    def _enviar_entrega_al_cliente(self, order):
        # Lógica para enviar un email al cliente con los enlaces de descarga
        pass

