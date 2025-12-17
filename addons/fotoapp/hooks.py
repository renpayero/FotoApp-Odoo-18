from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['fotoapp.plan'].sudo().search([])._ensure_plan_products()
    SaleSubscription = env['sale.subscription']
    SaleSubscription._fotoapp_migrate_legacy_plan_subscriptions()
    SaleSubscription._fotoapp_cleanup_orphan_references()
    SaleSubscription.search([('fotoapp_is_photographer_plan', '=', True)])._fotoapp_ensure_subscription_lines()
