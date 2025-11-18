from odoo import api, fields, models

from .utils import slugify_text


class TiendaFotoEvento(models.Model):
    _name = 'tienda.foto.evento'
    _description = 'Eventos de fotos'
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Nombre', required=True)
    fecha = fields.Datetime(string='Fecha del Evento', required=True)
    ciudad = fields.Char(string='Ciudad')
    estado_provincia = fields.Char(string='Estado / Provincia')
    pais_id = fields.Many2one('res.country', string='País')
    categoria_id = fields.Many2one(
        comodel_name='tienda.foto.categoria',
        string='Categoría',
        required=True
    )
    photographer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Fotógrafo',
        required=True,
        domain="[('is_photographer', '=', True)]"
    )
    descripcion = fields.Html(string='Descripción')
    image_cover = fields.Image(
        string='Portada del evento',
        max_width=1920,
        max_height=1080,
        attachment=True
    )
    precio_base = fields.Monetary(string='Precio base sugerido', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    carpeta_externa = fields.Char(string='Carpeta/Álbum Externo')
    website_slug = fields.Char(string='Slug para web', required=True)
    website_published = fields.Boolean(string='Publicado en web', default=False)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado')
    ], string='Estado', default='borrador')
    is_featured = fields.Boolean(string='Evento destacado')
    upload_token = fields.Char(string='Token de subida masiva')
    foto_ids = fields.One2many(
        comodel_name='tienda.foto.asset',
        inverse_name='evento_id',
        string='Fotos'
    )
    foto_count = fields.Integer(string='Cantidad de fotos', compute='_compute_foto_count')

    _sql_constraints = [
        ('website_slug_unique', 'unique(website_slug)', 'Ya existe un evento con el mismo slug.'),
    ]

    @api.depends('foto_ids')
    def _compute_foto_count(self):
        for event in self:
            event.foto_count = len(event.foto_ids)

    def _prepare_slug(self, value):
        base = value or (f"{self.name}-{self.id}" if (self.name and self.id) else self.name)
        return slugify_text(base, fallback='evento')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['website_slug'] = slugify_text(vals.get('website_slug') or vals.get('name'), fallback='evento')
        events = super().create(vals_list)
        events._ensure_upload_tokens()
        return events

    def write(self, vals):
        if vals.get('website_slug'):
            vals['website_slug'] = slugify_text(vals['website_slug'], fallback='evento')
        res = super().write(vals)
        if 'website_slug' in vals or 'name' in vals:
            self._ensure_upload_tokens()
        return res

    def _ensure_upload_tokens(self):
        for event in self.filtered(lambda e: not e.upload_token):
            fallback = slugify_text(f"{event.name}-{event.id}", fallback='evento')
            event.upload_token = self.env['ir.sequence'].next_by_code('tienda.foto.evento.upload') or fallback

    def action_publicar(self):
        self.write({'estado': 'publicado', 'website_published': True})

    def action_archivar(self):
        self.write({'estado': 'archivado', 'website_published': False})

    def action_volver_borrador(self):
        self.write({'estado': 'borrador'})