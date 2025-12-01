from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fotoapp_plan_id = fields.Many2one('fotoapp.plan', string='Plan FotoApp', copy=False)
