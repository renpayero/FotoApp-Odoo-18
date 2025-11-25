"""Legacy placeholder.

All Fotoapp website and photographer portal routes moved to modules under
`fotoapp.controllers`:

- gallery.py
- photographer_dashboard.py
- photographer_events.py
- photographer_albums.py
- photographer_assets.py
- portal_base.py

Order matters for Odoo auto-loading, so keep this stub file to avoid import
errors when the manifest or upgrades still references `controllers.controllers`.
This file intentionally contains no executable logic.
"""

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