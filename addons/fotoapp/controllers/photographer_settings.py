import logging

from odoo import http
from odoo.http import request

from .portal_base import PhotographerPortalMixin

_logger = logging.getLogger(__name__)


class PhotographerSettingsController(PhotographerPortalMixin, http.Controller):
    @http.route(
        ['/mi/fotoapp/configuracion/marca-agua'],
        type='http',
        auth='user',
        website=True,
        methods=['GET', 'POST']
    )
    def photographer_watermark_settings(self, **post):
        partner, denied = self._ensure_photographer()
        if not partner:
            return denied

        success_message = request.session.pop('fotoapp_watermark_success', False)
        errors = []
        values = {
            'partner': partner,
            'active_menu': 'settings',
            'errors': errors,
            'success': success_message,
        }

        if request.httprequest.method == 'POST':
            update_vals = {}
            watermark_file = request.httprequest.files.get('watermark_image')
            remove_image = post.get('remove_watermark') == '1'

            if watermark_file and watermark_file.filename:
                encoded = self._prepare_cover_image(watermark_file)
                if encoded:
                    update_vals['watermark_image'] = encoded
                else:
                    errors.append('No se pudo procesar la imagen cargada. Intenta con otro archivo.')
            elif remove_image:
                update_vals['watermark_image'] = False

            opacity_raw = post.get('watermark_opacity')
            scale_raw = post.get('watermark_scale')

            try:
                opacity_value = int(opacity_raw)
            except (TypeError, ValueError):
                opacity_value = None
            if opacity_value is None or opacity_value < 0 or opacity_value > 100:
                errors.append('La opacidad debe ser un número entre 0 y 100.')
            else:
                update_vals['watermark_opacity'] = opacity_value

            try:
                scale_value = float(scale_raw)
            except (TypeError, ValueError):
                scale_value = None
            if scale_value is None or scale_value <= 0:
                errors.append('La escala debe ser un número mayor a 0.')
            else:
                scale_value = max(0.05, min(scale_value, 1.0))
                update_vals['watermark_scale'] = scale_value

            if not errors and update_vals:
                partner.sudo().write(update_vals)
                request.session['fotoapp_watermark_success'] = 'Configuración de marca de agua guardada correctamente.'
                return request.redirect('/mi/fotoapp/configuracion/marca-agua')

        return request.render('fotoapp.photographer_watermark_settings', values)
