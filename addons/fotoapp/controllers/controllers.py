import base64
from datetime import datetime
import logging

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


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

	def _ensure_photographer(self):
		partner = self._get_current_photographer()
		if not partner:
			return None, request.render('fotoapp.gallery_photographer_required', {})
		return partner, None

	def _parse_datetime(self, value):
		_logger.warning(f"Parsing datetime value: {value}")
		if not value:
			return False
		# Navegadores pueden enviar distintos formatos (ej: ISO8601, mm/dd/yyyy con AM/PM).
		for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %I:%M %p", "%d/%m/%Y %H:%M"):
			try:
				return datetime.strptime(value, fmt)
			except ValueError:
				continue
		try:
			return fields.Datetime.to_datetime(value)
		except ValueError:
			return False

	def _get_event_for_partner(self, partner, event_id):
		return request.env['tienda.foto.evento'].sudo().search([
			('id', '=', event_id),
			('photographer_id', '=', partner.id),
		], limit=1)

	def _get_album_for_partner(self, partner, album_id):
		return request.env['tienda.foto.album'].sudo().search([
			('id', '=', album_id),
			('photographer_id', '=', partner.id),
		], limit=1)

	def _get_asset_for_partner(self, partner, asset_id):
		return request.env['tienda.foto.asset'].sudo().search([
			('id', '=', asset_id),
			('photographer_id', '=', partner.id),
		], limit=1)

	@http.route(['/mi/fotoapp', '/mi/fotoapp/dashboard'], type='http', auth='user', website=True)
	def photographer_dashboard(self, **kwargs):
		partner, denied = self._ensure_photographer()
		if not partner:
			return denied

		Event = request.env['tienda.foto.evento'].sudo()
		Album = request.env['tienda.foto.album'].sudo()
		Asset = request.env['tienda.foto.asset'].sudo()
		events = Event.search([
			('photographer_id', '=', partner.id)
		], order='create_date desc', limit=10)
		stats = {
			'total_events': Event.search_count([('photographer_id', '=', partner.id)]),
			'published_events': Event.search_count([('photographer_id', '=', partner.id), ('estado', '=', 'publicado')]),
			'albums': Album.search_count([('photographer_id', '=', partner.id)]),
			'photos': Asset.search_count([('photographer_id', '=', partner.id)]),
		}
		values = {
			'partner': partner,
			'events': events,
			'stats': stats,
			'active_menu': 'dashboard',
		}
		return request.render('fotoapp.photographer_dashboard', values)

	@http.route(['/mi/fotoapp/eventos'], type='http', auth='user', website=True)
	def photographer_event_list(self, estado=None, search=None, **kwargs):
		partner, denied = self._ensure_photographer()
		if not partner:
			return denied
		Event = request.env['tienda.foto.evento'].sudo()
		base_domain = [('photographer_id', '=', partner.id)]
		state_filter = estado if estado in {'borrador', 'publicado', 'archivado'} else False
		if state_filter:
			base_domain.append(('estado', '=', state_filter))
		search_term = (search or '').strip()
		if search_term:
			base_domain += ['|', ('name', 'ilike', search_term), ('categoria_id.name', 'ilike', search_term)]
		events = Event.search(base_domain, order='fecha desc, create_date desc')
		stats = {
			'all': Event.search_count([('photographer_id', '=', partner.id)]),
			'borrador': Event.search_count([('photographer_id', '=', partner.id), ('estado', '=', 'borrador')]),
			'publicado': Event.search_count([('photographer_id', '=', partner.id), ('estado', '=', 'publicado')]),
			'archivado': Event.search_count([('photographer_id', '=', partner.id), ('estado', '=', 'archivado')]),
		}
		values = {
			'partner': partner,
			'events': events,
			'active_menu': 'events',
			'state_filter': state_filter or 'all',
			'search': search_term,
			'stats': stats,
		}
		return request.render('fotoapp.photographer_event_list', values)

	@http.route(['/mi/fotoapp/eventos/nuevo'], type='http', auth='user', website=True, methods=['GET', 'POST'])
	def photographer_event_create(self, **post):
		partner, denied = self._ensure_photographer()
		if not partner:
			return denied

		categories = request.env['tienda.foto.categoria'].sudo().search([
			('estado', '!=', 'archivado'),
		], order='name')
		countries = request.env['res.country'].sudo().search([], order='name')
		values = {
			'partner': partner,
			'categories': categories,
			'countries': countries,
			'errors': [],
			'active_menu': 'events_new',
			'default': {
				'name': post.get('name', ''),
				'fecha': post.get('fecha', ''),
				'ciudad': post.get('ciudad', ''),
				'estado_provincia': post.get('estado_provincia', ''),
				'pais_id': post.get('pais_id'),
				'categoria_id': post.get('categoria_id'),
				'descripcion': post.get('descripcion', ''),
			}
		}

		if request.httprequest.method == 'POST':
			name = (post.get('name') or '').strip()
			categoria_id = post.get('categoria_id')
			fecha = self._parse_datetime(post.get('fecha'))
			cover = self._prepare_cover_image(post.get('image_cover'))
			if not name:
				values['errors'].append('El nombre del evento es obligatorio.')
			if not categoria_id:
				values['errors'].append('Debes seleccionar una categoría.')
			if not fecha:
				values['errors'].append('Debes indicar una fecha válida.')
			if not values['errors']:
				vals = {
					'name': name,
					'categoria_id': int(categoria_id),
					'fecha': fields.Datetime.to_string(fecha),
					'ciudad': post.get('ciudad'),
					'estado_provincia': post.get('estado_provincia'),
					'pais_id': int(post.get('pais_id')) if post.get('pais_id') else False,
					'descripcion': post.get('descripcion'),
					'photographer_id': partner.id,
					'website_published': False,
					'estado': 'borrador',
				}
				if cover:
					vals['image_cover'] = cover
				event = request.env['tienda.foto.evento'].sudo().create(vals)
				return request.redirect(f"/mi/fotoapp/evento/{event.id}")
		return request.render('fotoapp.photographer_event_create', values)

	@http.route(['/mi/fotoapp/evento/<int:event_id>'], type='http', auth='user', website=True, methods=['GET', 'POST'])
	def photographer_event_detail(self, event_id, **post):
		partner, denied = self._ensure_photographer()
		if not partner:
			return denied
		event = self._get_event_for_partner(partner, event_id)
		if not event:
			return request.not_found()
		categories = request.env['tienda.foto.categoria'].sudo().search([
			('estado', '!=', 'archivado')
		], order='name')
		countries = request.env['res.country'].sudo().search([], order='name')
		albums = request.env['tienda.foto.album'].sudo().search([
			('event_id', '=', event.id)
		], order='create_date desc')
		album_error = request.session.pop('fotoapp_album_error', False)
		values = {
			'partner': partner,
			'event': event,
			'albums': albums,
			'categories': categories,
			'countries': countries,
			'errors': [],
			'album_error': album_error,
			'active_menu': 'events',
		}

		if request.httprequest.method == 'POST':
			action = post.get('action') or 'update_event'
			redirect_url = f"/mi/fotoapp/evento/{event.id}"
			if action == 'update_event':
				fecha = self._parse_datetime(post.get('fecha'))
				categoria_id = post.get('categoria_id')
				if not categoria_id:
					values['errors'].append('Selecciona una categoría.')
				if not fecha:
					values['errors'].append('Ingresa una fecha válida.')
				if not values['errors']:
					update_vals = {
						'name': (post.get('name') or '').strip(),
						'fecha': fields.Datetime.to_string(fecha),
						'ciudad': post.get('ciudad'),
						'estado_provincia': post.get('estado_provincia'),
						'pais_id': int(post.get('pais_id')) if post.get('pais_id') else False,
						'descripcion': post.get('descripcion'),
						'categoria_id': int(categoria_id),
					}
					cover = self._prepare_cover_image(post.get('image_cover'))
					if cover:
						update_vals['image_cover'] = cover
					event.sudo().write(update_vals)
				else:
					return request.render('fotoapp.photographer_event_detail', values)
			elif action == 'publish_event':
				event.sudo().action_publicar()
			elif action == 'archive_event':
				event.sudo().action_archivar()
			elif action == 'delete_event':
				event.sudo().unlink()
				return request.redirect('/mi/fotoapp')
			return request.redirect(redirect_url)

		return request.render('fotoapp.photographer_event_detail', values)

	@http.route(['/mi/fotoapp/evento/<int:event_id>/album/nuevo'], type='http', auth='user', website=True, methods=['POST'])
	def photographer_album_create(self, event_id, **post):
		partner, denied = self._ensure_photographer()
		if not partner:
			return denied
		event = self._get_event_for_partner(partner, event_id)
		if not event:
			return request.not_found()
		name = (post.get('name') or '').strip()
		if not name:
			request.session['fotoapp_album_error'] = 'El nombre del álbum es obligatorio.'
		else:
			vals = {
				'name': name,
				'event_id': event.id,
				'partner_id': post.get('partner_id') or False,
				'customer_email': post.get('customer_email'),
			}
			request.env['tienda.foto.album'].sudo().create(vals)
		return request.redirect(f"/mi/fotoapp/evento/{event.id}")

	@http.route(['/mi/fotoapp/album/<int:album_id>'], type='http', auth='user', website=True, methods=['GET', 'POST'])
	def photographer_album_detail(self, album_id, **post):
		partner, denied = self._ensure_photographer()
		if not partner:
			return denied
		album = self._get_album_for_partner(partner, album_id)
		if not album:
			return request.not_found()
		if request.httprequest.method == 'POST' and (post.get('action') == 'delete_album'):
			event_id = album.event_id.id
			album.sudo().unlink()
			return request.redirect(f"/mi/fotoapp/evento/{event_id}")
		values = {
			'partner': partner,
			'album': album,
			'photos': album.asset_ids,
			'errors': [],
			'active_menu': 'events',
			'can_publish_album': album.state in {'draft', 'editing', 'proofing'},
		}
		if request.httprequest.method == 'POST':
			action = post.get('action')
			should_redirect = True
			if action == 'update_album':
				album.sudo().write({
					'name': (post.get('name') or '').strip(),
					'is_private': 'is_private' in post,
					'download_limit': int(post.get('download_limit') or 0),
				})
			elif action == 'publish_album':
				album.sudo().action_publish()
			elif action == 'archive_album':
				album.sudo().action_archive()
			elif action == 'upload_photo':
				image = self._prepare_cover_image(post.get('image_file'))
				precio = post.get('price')
				if not image:
					values['errors'].append('Debes seleccionar una imagen para subir.')
				try:
					precio = float(precio or 0.0)
				except ValueError:
					values['errors'].append('El precio debe ser numérico.')
				if not values['errors']:
					asset_vals = {
						'evento_id': album.event_id.id,
						'precio': precio,
						'imagen_original': image,
						'album_ids': [(4, album.id)],
					}
					request.env['tienda.foto.asset'].sudo().create(asset_vals)
				else:
					should_redirect = False
			elif action in {'archive_photo', 'publish_photo'}:
				photo_id = int(post.get('photo_id')) if post.get('photo_id') else False
				photo = self._get_asset_for_partner(partner, photo_id)
				if photo:
					values_to_write = {}
					if action == 'archive_photo':
						values_to_write.update({'lifecycle_state': 'archived', 'website_published': False, 'publicada': False})
					else:
						values_to_write.update({'lifecycle_state': 'published', 'publicada': True})
					photo.sudo().write(values_to_write)
			if should_redirect:
				return request.redirect(f"/mi/fotoapp/album/{album.id}")
			values['photos'] = album.asset_ids
			values['can_publish_album'] = album.state in {'draft', 'editing', 'proofing'}
		return request.render('fotoapp.photographer_album_detail', values)

	@http.route(['/mi/fotoapp/fotos/archivadas'], type='http', auth='user', website=True, methods=['GET', 'POST'])
	def photographer_archived_photos(self, **post):
		partner, denied = self._ensure_photographer()
		if not partner:
			return denied
		Asset = request.env['tienda.foto.asset'].sudo()
		domain = [
			('photographer_id', '=', partner.id),
			('lifecycle_state', '=', 'archived')
		]
		search_term = (request.params.get('search') or '').strip()
		if search_term:
			domain += ['|', '|',
				('numero_dorsal', 'ilike', search_term),
				('evento_id.name', 'ilike', search_term),
				('album_ids.name', 'ilike', search_term)
			]
		photos = Asset.search(domain, order='write_date desc')
		if request.httprequest.method == 'POST':
			action = post.get('action')
			photo = self._get_asset_for_partner(partner, int(post.get('photo_id')))
			if photo:
				if action == 'restore':
					photo.sudo().write({'lifecycle_state': 'ready_for_sale'})
				elif action == 'delete':
					photo.sudo().unlink()
			return request.redirect('/mi/fotoapp/fotos/archivadas')
		values = {'partner': partner, 'photos': photos, 'active_menu': 'archived', 'search': search_term}
		return request.render('fotoapp.photographer_archived_photos', values)