import logging

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class FotoappGalleryController(http.Controller):
    def _get_categories(self):
        return request.env['tienda.foto.categoria'].sudo().search([
            ('website_published', '=', True),
            ('estado', '!=', 'archivado'),
        ], order='sequence, name')

    def _get_public_albums(self, event):
        return request.env['tienda.foto.album'].sudo().search([
            ('event_id', '=', event.id),
            ('state', '=', 'published'),
            ('is_private', '=', False),
        ], order='create_date desc')

    @http.route(['/galeria'], type='http', auth='public', website=True)
    def gallery_home(self, **kwargs):
        categories = self._get_categories()
        featured_events = request.env['tienda.foto.evento'].sudo().search([
            ('website_published', '=', True),
            ('estado', '=', 'publicado'),
            ('is_featured', '=', True),
        ], limit=6, order='fecha desc')
        recent_events = request.env['tienda.foto.evento'].sudo().search([
            ('website_published', '=', True),
            ('estado', '=', 'publicado'),
        ], limit=8, order='published_at desc, fecha desc')
        values = {
            'categories': categories,
            'featured_events': featured_events,
            'recent_events': recent_events,
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
        albums = self._get_public_albums(event)
        values = {
            'event': event,
            'albums': albums,
            'breadcrumb': [
                {'label': 'Galería', 'url': '/galeria'},
                {'label': event.categoria_id.name, 'url': f"/galeria/categoria/{event.categoria_id.slug}"},
            ],
        }
        return request.render('fotoapp.gallery_event_detail', values)

    @http.route(['/galeria/evento/<string:event_slug>/album/<int:album_id>'], type='http', auth='public', website=True)
    def gallery_album(self, event_slug, album_id, **kwargs):
        event = request.env['tienda.foto.evento'].sudo().search([
            ('website_slug', '=', event_slug),
            ('website_published', '=', True),
        ], limit=1)
        if not event:
            return request.not_found()
        album = request.env['tienda.foto.album'].sudo().search([
            ('id', '=', album_id),
            ('event_id', '=', event.id),
            ('state', '=', 'published'),
            ('is_private', '=', False),
        ], limit=1)
        if not album:
            return request.not_found()
        photos = request.env['tienda.foto.asset'].sudo().search([
            ('album_ids', 'in', album.id),
            ('website_published', '=', True),
            ('lifecycle_state', '!=', 'archived'),
        ], order='id desc')
        values = {
            'event': event,
            'album': album,
            'photos': photos,
            'breadcrumb': [
                {'label': 'Galería', 'url': '/galeria'},
                {'label': event.categoria_id.name, 'url': f"/galeria/categoria/{event.categoria_id.slug}"},
                {'label': event.name, 'url': f"/galeria/evento/{event.website_slug}"},
            ],
        }
        return request.render('fotoapp.gallery_album_detail', values)

    @http.route(['/galeria/foto/<int:photo_id>/cart/add'], type='http', auth='public', website=True, methods=['POST'])
    def gallery_add_photo_to_cart(self, photo_id, **post):
        quantity = 1
        try:
            quantity = max(1, int(post.get('quantity', 1)))
        except (TypeError, ValueError):
            quantity = 1
        photo = request.env['tienda.foto.asset'].sudo().search([
            ('id', '=', photo_id),
            ('website_published', '=', True),
            ('lifecycle_state', '!=', 'archived'),
        ], limit=1)
        referer = post.get('redirect') or request.httprequest.referrer or '/galeria'
        if not photo:
            request.session['website_sale_cart_warning'] = _('La foto seleccionada no está disponible.')
            return request.redirect(referer)
        product = photo.ensure_sale_product()[:1]
        if not product:
            request.session['website_sale_cart_warning'] = _('No se pudo preparar la foto para la venta. Intentalo nuevamente en unos instantes.')
            return request.redirect(referer)
        order = request.website.sale_get_order(force_create=True)
        result = order._cart_update(product_id=product.id, add_qty=quantity, set_qty=False)
        line_id = result.get('line_id')
        if line_id:
            line = request.env['sale.order.line'].sudo().browse(line_id)
            line.write({'foto_asset_id': photo.id})
        request.session['website_sale_cart_success'] = _('Agregaste %s al carrito.') % (photo.name or _('Foto'))
        return request.redirect(referer)
