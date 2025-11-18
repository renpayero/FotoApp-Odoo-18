import base64

from odoo import http
from odoo.http import request


class FotoappWebsite(http.Controller):
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

	def _get_current_photographer(self):
		partner = request.env.user.partner_id
		if not partner or not partner.is_photographer:
			return None
		return partner

	def _prepare_cover_image(self, uploaded_file):
		if not uploaded_file or not hasattr(uploaded_file, 'read'):
			return False
		binary = uploaded_file.read()
		if not binary:
			return False
		return base64.b64encode(binary)

	@http.route(['/mi/galeria/categorias/nueva'], type='http', auth='user', website=True, methods=['GET', 'POST'])
	def gallery_category_create(self, **post):
		partner = self._get_current_photographer()
		if not partner:
			return request.render('fotoapp.gallery_photographer_required', {})

		values = {
			'errors': [],
			'default': {
				'name': post.get('name', ''),
				'description': post.get('description', ''),
				'website_description': post.get('website_description', ''),
				'publish_now': post.get('publish_now') == '1',
			}
		}

		if request.httprequest.method == 'POST':
			name = (post.get('name') or '').strip()
			website_description = post.get('website_description') or ''
			description = post.get('description') or ''
			publish_now = post.get('publish_now') == '1'
			cover_file = post.get('image_cover')
			cover_image = self._prepare_cover_image(cover_file)

			if not name:
				values['errors'].append('El nombre es obligatorio.')
			if not cover_image:
				values['errors'].append('Debes seleccionar una imagen de portada.')

			if not values['errors']:
				vals = {
					'name': name,
					'description': description,
					'website_description': website_description,
					'image_cover': cover_image,
					'owner_id': partner.id,
					'website_published': publish_now,
					'estado': 'publicado' if publish_now else 'borrador',
				}
				category = request.env['tienda.foto.categoria'].sudo().create(vals)
				return request.redirect(f"/galeria/categoria/{category.slug}")

		return request.render('fotoapp.gallery_category_create', values)