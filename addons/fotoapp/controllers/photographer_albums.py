import logging

from odoo import http
from odoo.http import request

from .portal_base import PhotographerPortalMixin

_logger = logging.getLogger(__name__)


class PhotographerAlbumsController(PhotographerPortalMixin, http.Controller):
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
