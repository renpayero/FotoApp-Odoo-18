from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    foto_asset_id = fields.Many2one('tienda.foto.asset', string='Foto asociada', ondelete='set null')
    foto_photographer_id = fields.Many2one('res.partner', string='Fotógrafo', related='foto_asset_id.photographer_id', store=True, readonly=True)
