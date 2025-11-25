import logging

from odoo import http
from odoo.http import request

from .portal_base import PhotographerPortalMixin

_logger = logging.getLogger(__name__)


class PhotographerDashboardController(PhotographerPortalMixin, http.Controller):
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
