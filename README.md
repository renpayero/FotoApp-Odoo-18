### DESCRIPCION

FotoApp es un módulo vertical para Odoo 18 que permite a fotógrafos publicar, vender y entregar fotos/álbumes desde el website, mientras la plataforma administra suscripciones, comisiones y facturación interna. Incluye portal de fotógrafo, galería pública, ecommerce con control de un solo fotógrafo por carrito y automatiza la generación de deudas y facturas de los planes, con pasarela Mercado Pago para cobros.

### CONTEXTO

- Modelo SaaS: la plataforma factura al fotógrafo sus planes de suscripción; no hay emisión desde un POS. La app pública vende fotos a clientes finales, separada de la facturación interna a fotógrafos.
- Datos iniciales: se cargan planes Freemium, Básico, Pro y Enterprise (ARS), más plantilla de suscripción OCA y producto de renovación para el portal de deudas.
- Cron jobs: generar deudas de suscripción, pasar a gracia/expirada, y facturar deudas pendientes.
- Website: catálogo de eventos/álbumes, landing de planes y vistas de compra/descarga.
- Portal de fotógrafo: dashboard, eventos, álbumes, fotos, deudas, pedidos y perfil con OAuth de Mercado Pago.

### STACK TECNOLOGICO

- Base: Odoo 18 (imagen oficial), Postgres 15, Docker/Compose.
- Addons clave: subscription_oca (suscripciones), payment_mercado_pago (pasarela), website/website_sale/portal/mail/crm.
- Python libs extra: pillow, requests.
- Config: odoo.conf habilita proxy_mode y añade ruta /mnt/extra-addons. Env ADMIN_PASSWORD en compose para admin inicial.
- Licencia: AGPL-3 (en el manifest).

### FUNCIONALIDADES 

- Planes y suscripciones
	- Planes FotoApp con producto/template sincronizados, diario, cuenta de ingresos e impuestos configurables. Seeding de planes Freemium/Básico/Pro/Enterprise.
	- Suscripciones de fotógrafos (sale.subscription) con estados trial/active/grace y límites de almacenamiento/eventos/fotos.
	- Cron de cobro: genera fotoapp.debt y al instante crea facturas de cliente (account.move out_invoice) usando el producto del plan.
- Deudas y facturación interna
	- Modelo fotoapp.debt con vínculo a pedido, factura y pagos; cron adicional factura deudas pendientes.
	- Portal de deudas: pagar renovaciones via carrito con producto de renovación; historial de pagos.
- Cobros Mercado Pago
	- Flujo Marketplace (split): metadata de plan/fotógrafo/comisión en payment.transaction; usa seller token del fotógrafo (OAuth desde el portal).
	- Al confirmar pedido con transacción done, marca deudas pagadas y registra account.payment en diario de pasarela configurado.
- Portal de fotógrafo
	- Dashboard con métricas de eventos/álbumes/fotos/almacenamiento y comisión del plan.
	- Gestión de eventos (slug, portada, ciclo de vida), álbumes (privados/públicos, tokens de cliente), fotos (watermark automática, pricing, producto ecommerce sincronizado, control de almacenamiento y token portal), y pedidos históricos.
	- Perfil y payout: datos biográficos, redes, preferencia de cobro, conexión OAuth a Mercado Pago y configuración de marca de agua.
- Galería pública y ecommerce
	- Categorías y eventos publicados, álbumes públicos, ficha de foto con add-to-cart; restricción: un carrito solo admite fotos de un fotógrafo.
	- Página de planes con CTA al carrito usando la variante del plan.
	- Descarga post-compra: enlace a fotos sin marca de agua desde la confirmación y página dedicada.
- Fiscal/AFIP (scaffolding)
	- En ajustes: modo AFIP (testing/producción), punto de venta AFIP, certificados y clave privada como adjuntos, passphrase, diario Mercado Pago.
	- En partner fotógrafo: campos fiscales (CUIT, condición IVA, domicilio fiscal, PDV preferido) para futuras facturas electrónicas.

### INFORMACION ADICIONAL

- Rutas relevantes: addons montados en /mnt/extra-addons; manifiesto en addons/fotoapp/__manifest__.py. Config Odoo en odoo.conf. Compose expone 8069 y monta odoo-data/db-data como volúmenes.
- Secuencias y productos: secuencia fotoapp.debt, producto de renovación, plantilla de suscripción base; creación de tokens de portal/descarga para eventos, álbumes y fotos.
- Seguridad: accesos de usuario base.group_user a modelos clave (planes, eventos, álbumes, fotos, deudas, statements).
- Advertencias operativas: para facturar deudas se requiere diario de venta y cuenta de ingresos en el plan; para registrar pagos MP, configurar diario de pasarela en Ajustes FotoApp.
- Admin inicial: variable ADMIN_PASSWORD en compose; usuario admin se crea con esa clave.

### LISTA DE TAREAS

- ✅ Migración y sincronización de planes/productos/plantillas de suscripción.
- ✅ Generación de deudas y facturas internas por suscripción (cron y on-create).
- ✅ Registro automático de pagos Mercado Pago contra facturas y deudas.
- ✅ Portal de fotógrafo (eventos, álbumes, fotos, pedidos, perfil, deudas) y galería pública/ecommerce.
- 🚧 Integrar emisión electrónica AFIP con los parámetros ya guardados (usar PDV, certificado, clave, passphrase).
- 🚧 Afinar reportes/estados contables de fotógrafos (liquidaciones y conciliaciones cruzadas).


### COMANDOS ESCENCIALES

RESET BASE DE DATOS:
docker compose exec odoo odoo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo -d fotoapp -u fotoapp --stop-after-init

Para abrir el odoo shell:
docker compose exec odoo odoo shell --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo -d fotoapp

----------

from odoo import fields

subs = env['sale.subscription'].browse(24)
subs.write({'next_billing_date': fields.Date.today()})  # forzá la fecha
env['sale.subscription'].fotoapp_cron_generate_subscription_debts()
debts = env['fotoapp.debt'].search([('subscription_id', '=', subs.id)])
debts.read(['billing_date', 'state', 'partner_id'])

-----------

# Archivar forzado (simula +30 días sin ventas)
from odoo import fields
from dateutil.relativedelta import relativedelta

asset = env['tienda.foto.asset'].search([('numero_dorsal','=','28')], limit=1)
old = fields.Datetime.now() - relativedelta(days=31)
asset.write({'publicada_por_ultima_vez': old, 'last_sale_date': False})
env['tienda.foto.asset'].cron_manage_photo_lifecycle()
env.cr.commit()  # <--- commit necesario

asset = env['tienda.foto.asset'].browse(asset.id)
asset.read(['lifecycle_state','publicada','website_published','publicada_por_ultima_vez','last_sale_date'])

## explicacion
- from odoo import fields: importa utilidades de Odoo para manejar fechas/horas.
- from dateutil.relativedelta import relativedelta: importa un helper para restar periodos (p.ej. días).
- asset = env['tienda.foto.asset'].search([('numero_dorsal','=','28')], limit=1): busca la foto con dorsal 28.
- old = fields.Datetime.now() - relativedelta(days=31): calcula una fecha/hora 31 días atrás.
- asset.write({'publicada_por_ultima_vez': old, 'last_sale_date': False}): fuerza que la última publicación sea hace 31 días y borra cualquier fecha de última venta.
- env['tienda.foto.asset'].cron_manage_photo_lifecycle(): ejecuta el cron de ciclo de vida para archivar/eliminar según reglas.
- nv.cr.commit(): confirma los cambios en la base (sin esto, el web no los vería).
- asset = env['tienda.foto.asset'].browse(asset.id): vuelve a obtener el registro desde la base.
- asset.read(['lifecycle_state','publicada','website_published','publicada_por_ultima_vez','last_sale_date']): lee y muestra los campos clave para verificar el estado final.

# Eliminar forzado (simula +15 días archivada)
from odoo import fields
from dateutil.relativedelta import relativedelta

asset = env['tienda.foto.asset'].search([('numero_dorsal','=','28')], limit=1)
asset.action_archive()  # asegura estado archivado
asset.write({'archived_at': fields.Datetime.now() - relativedelta(days=16)})
env['tienda.foto.asset'].cron_manage_photo_lifecycle()
env.cr.commit()

asset.exists() 

## explicacion

- from odoo import fields: importa utilidades de Odoo para manejar fechas/horas.
- from dateutil.relativedelta import relativedelta: helper para restar periodos (días en este caso).
- asset = env['tienda.foto.asset'].search([('numero_dorsal','=','28')], limit=1): busca la foto con dorsal 28.
- asset.action_archive(): la deja en estado archivado y apaga visibilidad.
- asset.write({'archived_at': fields.Datetime.now() - relativedelta(days=16)}): simula que fue archivada hace 16 días (más de los 15 configurados).
- env['tienda.foto.asset'].cron_manage_photo_lifecycle(): ejecuta el cron de ciclo de vida; al ver que pasaron los días - configurados, elimina la foto.
- env.cr.commit(): confirma la eliminación en la base de datos.
- asset.exists(): devuelve False si la foto fue borrada, True si aún existe.

