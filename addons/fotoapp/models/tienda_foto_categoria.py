from odoo import api, fields, models

from .utils import slugify_text


class TiendaFotoCategoria(models.Model):
    _name = 'tienda.foto.categoria'
    _description = 'Categorías de fotos'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción interna')
    website_description = fields.Html(string='Descripción para el sitio web')
    sequence = fields.Integer(string='Secuencia', default=10)
    image_cover = fields.Image(
        string='Imagen de portada',
        max_width=1920,
        max_height=1080,
        attachment=True,
        help='Imagen mostrada en tarjetas de la web.'
    )
    slug = fields.Char(string='Slug', required=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado')
    ], string='Estado', default='borrador')
    website_published = fields.Boolean(string='Publicado en web', default=False)
    owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Fotógrafo responsable',
        readonly=True
    )
    evento_ids = fields.One2many(
        comodel_name='tienda.foto.evento',
        inverse_name='categoria_id',
        string='Eventos'
    )
    event_count = fields.Integer(string='Total de eventos', compute='_compute_event_count')

    _sql_constraints = [
        ('slug_unique', 'unique(slug)', 'El slug debe ser único.'),
    ]

    @api.depends('evento_ids')
    def _compute_event_count(self):
        for record in self:
            record.event_count = len(record.evento_ids)

    def _prepare_slug(self, value):
        slug_base = value or self.name or ''
        return slugify_text(slug_base, fallback='categoria')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['slug'] = self._prepare_slug(vals.get('slug') or vals.get('name'))
            if not vals.get('owner_id') and self.env.user.partner_id:
                vals['owner_id'] = self.env.user.partner_id.id
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('slug'):
            vals['slug'] = self._prepare_slug(vals['slug'])
        return super().write(vals)

    def action_publicar(self):
        self.write({'estado': 'publicado', 'website_published': True})

    def action_archivar(self):
        self.write({'estado': 'archivado', 'website_published': False})

    def action_volver_borrador(self):
        self.write({'estado': 'borrador'})