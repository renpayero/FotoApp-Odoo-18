# Cliente FotoApp

Guía rápida para dejar la instancia lista para el fotógrafo y sus clientes.

## 1. Crear el usuario administrador
1. Entra a la instancia: `http://<tu-vps>:8069`.
2. Usa `admin` y la contraseña `ADMIN_PASSWORD` definida en `compose.yaml` para ingresar como superusuario.
3. Ve a Ajustes > Usuarios y empresas > Usuarios.
4. Duplica o crea un usuario con permisos de Administrador y asigna el correo y nombre del cliente (p. ej. `fotografo@dominio.com`).
5. Revisa que el usuario tenga acceso a Ventas, Sitio Web, Portal, CRM y Contabilidad, ya que necesita configurar catálogos y deudas.

## 2. Configurar credenciales de Mercado Pago
1. Regístrate en https://www.mercadopago.com.ar/developers/es y verifica la cuenta.
2. En el panel de Mercado Pago crea un proyecto y obtén el `PUBLIC KEY` y el `ACCESS TOKEN` (ambos modo sandbox y producción).
3. En Odoo ve a Ajustes > Sitio web > Compra - Pago > Ver otros proveedores > Activa mercadopago (en activado).
4. Copia los tokens correspondientes en `Access Token`.
5. Para el modo producción cambia a `Environment: Production` y pega los valores definitivos. Asegúrate de marcar el diario contable apropiado.
6. En Odoo ve a Ajustes > Ajustes generales > Mercado Pago Marketplace. Y completa las credenciales con las crecenciales de mercado pago developers.
7. Navega a FotoApp > Configuración > Perfil de fotógrafo y haz clic en "Conectar con Mercado Pago" para permitir el flujo split; cuando completes la OAuth recibirás el `seller_token` necesario para cobrar al fotógrafo.

## 3. Configurar la casilla de email
1. Activa el modo desarrollador.
2. Ve a Ajustes > Técnico > Correo > Servidores de correo saliente y crea un nuevo registro.
3. Usa Gmail (u otro proveedor) pero asegúrate de tener una contraseña de aplicación si usas 2FA.
4. Completa los campos clave según el ejemplo mostrado:

| Campo | Valor sugerido |
| --- | --- |
| Nombre | Gmail SMTP |
| Filtro DE | `nombredeemail@gmail.com` (o la dirección oficial de la marca) |
| Autenticar con | Nombre de usuario |
| Cifrado de la conexión | TLS (STARTTLS) |
| Servidor SMTP | smtp.gmail.com |
| Puerto SMTP | 587 |
| Nombre de usuario | la misma dirección de correo |
| Contraseña | contraseña de `aplicación` generada desde Gmail |
| Convertir adjuntos a enlaces | 0,00 MB (opcional) |

5. Guarda y haz clic en "Probar conexión"; si el proveedor lo exige, activa acceso para apps menos seguras o usa OAuth según corresponda.

## 4. Cargar fotos de portada de categorías y planes
1. En el portal, ve a FotoApp > Catalogo > Categorías. Y edita cada categoría para subir la imagen de portada. Puedes usar JPG/PNG optimizados.
2. Para planes Planes > Configurar Planes, utiliza la pestaña de imágenes del producto o template asociado para subir la portada que se mostrará en el sitio web.
3. Aprovecha la vista de sitio web para comprobar cómo se ven las imágenes (usa `https://<tu-vps>:8069/s` y navega por galerías). Ajusta tamaño y formato si queda deformado.

## 5. Configurar web.base.url
1. Asegúrate de que la instancia se accede siempre desde un dominio fijo (ej. `https://fotos.ejemplo.com`). En production no uses IPs ni http suelto.
2. Si usas un proxy inverso (Nginx/Traefik/Cloudflare), configúralo para reenviar encabezados `Host`, `X-Forwarded-Proto` y `X-Forwarded-Host` hacia Odoo.
3. En Ajustes > Técnico > Parámetros del sistema.  encuentra el campo`web.base.url` y fíjalo a la URL pública (con https si aplica).
4. En Ajustes > Sitio web > Información del sitio web > Dominio. Completa el campo con el mismo URL.
4. Reinicia el contenedor Odoo cuando cambies esta variable para que `web.base.url` se propague a los enlistamientos de correo, enlaces de pago y enlaces seguros.