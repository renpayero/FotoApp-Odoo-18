import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class FotoappGalleryController(http.Controller):
    def _get_categories(self):
        return request.env['tienda.foto.categoria'].sudo().search([
            ('website_published', '=', True),
            ('estado', '!=', 'archivado'),
        ], order='sequence, name')

    @http.route(['/galeria'], type='http', auth='public', website=True)
    def gallery_home(self, **kwargs):
        categories = self._get_categories()
        featured_events = request.env['tienda.foto.evento'].sudo().search([
            ('website_published', '=', True),
            ('estado', '=', 'publicado'),
            ('is_featured', '=', True),
        ], limit=6, order='fecha desc')
        values = {
            'categories': categories,
            'featured_events': featured_events,
        }
        return request.render('fotoapp.gallery_categories', values)

    @http.route(['/galeria/categoria/<string:slug>'], type='http', auth='public', website=True)
    def gallery_category(self, slug, **kwargs):
        category = request.env['tienda.foto.categoria'].sudo().search([
            ('slug', '=', slug),
            ('website_published', '=', True),
        ], limit=1)
        if not category:
            return request.not_found()
        events = request.env['tienda.foto.evento'].sudo().search([
            ('categoria_id', '=', category.id),
            ('website_published', '=', True),
            ('estado', '=', 'publicado'),
        ], order='fecha desc')
        values = {
            'category': category,
            'events': events,
            'breadcrumb': [
                {'label': 'Galería', 'url': '/galeria'},
            ],
        }
        return request.render('fotoapp.gallery_category_detail', values)

    @http.route(['/galeria/evento/<string:slug>'], type='http', auth='public', website=True)
    def gallery_event(self, slug, **kwargs):
        event = request.env['tienda.foto.evento'].sudo().search([
            ('website_slug', '=', slug),
            ('website_published', '=', True),
        ], limit=1)
        if not event:
            return request.not_found()
        photos = request.env['tienda.foto.asset'].sudo().search([
            ('evento_id', '=', event.id),
            ('website_published', '=', True),
        ], order='sequence, id desc')
        values = {
            'event': event,
            'photos': photos,
            'breadcrumb': [
                {'label': 'Galería', 'url': '/galeria'},
                {'label': event.categoria_id.name, 'url': f"/galeria/categoria/{event.categoria_id.slug}"},
            ],
        }
        return request.render('fotoapp.gallery_event_detail', values)
