 # FotoApp para Odoo 18

FotoApp es un módulo vertical para Odoo 18 que permite a fotógrafos publicar, vender y entregar fotos/álbumes desde el portal público mientras la plataforma administra suscripciones, comisiones y facturación interna. Esta PoC combina ecommerce, portal de fotógrafos, control financiero (deudas/facturas) y pasarela Mercado Pago con split para cobrar clientes finales y liquidar fotógrafos.

## Contenido
- `Requisitos`: componentes del stack, variables de entorno y dependencias.
- `Instalación rápida`: pasos necesarios para levantar la PoC con Docker Compose.
- `Resumen funcional`: flujos clave implementados.
- `Notas de operación`: recordatorios para QA y monitoreo.

## Requisitos
1. **Infraestructura mínima**: VPS Linux con Docker Engine 26+ y Docker Compose v2.
2. **Base de datos**: Postgres 15 (el servicio `db` del Compose ya expone el puerto 5432).
3. **SMTP**: una casilla funcional para enviar correos de confirmación y descarga.
4. **Variables de entorno**:
   - `ADMIN_PASSWORD`: contraseña del superusuario `admin` creado al primer arranque.
   - `ODOO_DB_HOST`, `ODOO_DB_PORT`, `ODOO_DB_USER`, `ODOO_DB_PASSWORD` (definidas en `compose.yaml`).
5. **Dependencias**: además de los módulos estándar de Odoo, FotoApp depende de `subscription_oca`, `payment_mercado_pago`, `website_sale`, `portal`, `mail`, `crm`, `product` y `account`.

## Instalación rápida
1. Clonar este repositorio dentro de `/mnt/extra-addons` (el volumen que monta el contenedor Odoo).
2. Ajustar `compose.yaml` y `odoo.conf` con los datos de su entorno (puertos, SMTP, claves, etc.).
3. Levantar la BD y Odoo: `docker compose up -d db odoo`.
4. Cargar el módulo con datos semilla: `docker compose exec odoo odoo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo -d fotoapp -u fotoapp --stop-after-init`.
5. Entrar en `http://<vps>:8069`, usuario `admin`, contraseña = `ADMIN_PASSWORD`.
6. Verificar que los planes Freemium/Básico/Pro/Enterprise y eventos de ejemplo existan en `Ventas > Planes` y `Website > Categorías`.

## Resumen funcional
- **Portal de fotógrafos**: dashboard con métricas, eventos, álbumes, fotos, deudas, pedidos y sincronización con Mercado Pago (OAuth + seller token).
- **Planes y suscripciones**: estados trial/active/grace, límites de almacenamiento/eventos/fotos y cron jobs que crean deudas (`fotoapp.debt`) y facturan automáticamente (`account.move`).
- **Deudas y facturación interna**: cada deuda tiene vínculo con pedido/factura; el portal permite renovar planes via carrito y registra `account.payment` en el diario de la pasarela.
- **Ecommerce controlado**: galerías públicas, limitación de carrito a un solo fotógrafo, descargas seguras post compra y vínculo de correo al final del checkout.
- **Pasarela Mercado Pago**: pagos split, metadata del plan y fotógrafo en `payment.transaction`, validación de token y seguimiento por el controlador `checkout_guest`.
- **Checkout guest**: botón deshabilitado hasta validar correo, campo oculto `guest_email` enviado vía JS y registrado en el partner antes de crear la transacción.

## Notas de operación
- **Frontend**: `fotoapp/static/src/js/payment_guest_email.js` amplía `PaymentForm` para pasar `guest_email` al RPC y se incluye en `web.assets_frontend` mediante `views/assets.xml`.
- **Controladores**: `FotoappWebsiteSale` extiende `WebsiteSale` solo para carritos invitados; los usuarios logueados siguen el flujo estándar.
- **Logs**: revisar `FotoApp shop_payment_transaction - guest email` en `odoo.log` para confirmar que el backend recibió el correo.
- **Cron jobs**: asegurar que `fotoapp.debt_cron`, `fotoapp.lifecycle_cron` y cualquier cron de entrega estén activos (`Ajustes > Automatización > Cron`).
- **Despliegues**: use HTTPS, configure `web.base.url`, ajuste `payment_mercado_pago` a producción y verifique envíos de correo/post-compra.

## Próximos pasos
1. Validar el flujo completo de fotos/álbumes y la notificación posterior a la compra.
2. Documentar la configuración del cliente (ver `README_CLIENT.md`).
3. Mantener un seguimiento de incidencias pendientes en la lista de tareas del repositorio.

