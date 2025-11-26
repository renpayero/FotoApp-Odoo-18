# FotoApp – Módulo de Fotografía para Odoo 18 (Front-End Only)

docker compose exec odoo odoo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo -d fotoapp -u fotoapp --stop-after-init

Módulo personalizado para **Odoo 18 Community** que permite a múltiples fotógrafos vender sus fotos con marca de agua usando el **website + e-commerce** de Odoo, integrando **Mercado Pago** como pasarela de pago y **CRM por fotógrafo** para registrar las ventas como oportunidades ganadas.

Todo el flujo operativo de los fotógrafos se realiza **desde el front-end** (website), dejando el back-end solo para tareas administrativas.

---

## Índice.

1. [Alcance General](#1-alcance-general)  
2. [Actores del Sistema](#2-actores-del-sistema)  
3. [Suposiciones y Dependencias](#3-suposiciones-y-dependencias)  
4. [Requisitos Funcionales (RF)](#4-requisitos-funcionales-rf)  
   - [4.1 Categorías Predefinidas](#41-categorías-predefinidas)  a
   - [4.2 Página de Inicio (Home)](#42-página-de-inicio-home)  
   - [4.3 Páginas de Navegación Pública](#43-páginas-de-navegación-pública)  
   - [4.4 Gestión del Contenido por Fotógrafo (Front-End)](#44-gestión-del-contenido-por-fotógrafo-front-end)  
   - [4.5 Planes de Fotógrafo y Comisión](#45-planes-de-fotógrafo-y-comisión)  
   - [4.6 Venta de Fotos, Mercado Pago y Entrega](#46-venta-de-fotos-mercado-pago-y-entrega)  
   - [4.7 Ciclo de Vida de las Fotos](#47-ciclo-de-vida-de-las-fotos-publicación-archivado-eliminación)  
   - [4.8 CRM por Fotógrafo](#48-crm-por-fotógrafo)  
5. [Instalación](#5-instalación)  
6. [Configuración Inicial](#6-configuración-inicial)  
7. [Uso del Módulo](#7-uso-del-módulo)  
8. [Roadmap / Próximos pasos](#8-roadmap--próximos-pasos)  
9. [Licencia](#9-licencia)  

---

## 1. Alcance General

El módulo de fotografía se integra al **100% en el front-end** de Odoo, usando **Website + e-commerce** como base.

- Los **fotógrafos** gestionan sus eventos, álbumes, fotos y marca de agua **solo desde el website** (no usan el back-end para la operación diaria).
- El **back-end** se utiliza únicamente para tareas administrativas:
  - Carga y mantenimiento de **categorías** y sus portadas.
  - Configuración de **planes de fotógrafo**, tiempos de archivado/eliminación, comisiones, etc.
  - Gestión de **facturación de comisiones** y suspensión de cuentas.

Objetivo principal:

> Permitir que múltiples fotógrafos, cada uno con su propio perfil, puedan:
> - Seleccionar categorías predefinidas para sus eventos.  
> - Crear eventos y álbumes.  
> - Subir fotos masivamente con marca de agua automática.  
> - Vender sus fotos desde su perfil público y desde páginas de evento/álbum.  
> - Registrar las ventas como oportunidades ganadas en su propio CRM.  
> - Entregar automáticamente la foto sin marca de agua al comprador una vez pagada vía Mercado Pago.  
> - Operar bajo un **plan de suscripción** (Freemium, Básico, Premium, Enterprise) con límites de fotos y comisiones.

---

## 2. Actores del Sistema

### A1. Visitante (no autenticado)

- Navega **categorías**, **eventos** y **fotógrafos**.
- Ve eventos y fotos públicas (con marca de agua).
- Puede agregar fotos al carrito.
- Puede avanzar al checkout como cliente (creando/ingresando cuenta).

### A2. Cliente / Comprador

- Usuario autenticado **sin plan de fotógrafo**.
- Puede comprar fotos.
- Recibe por email las fotos compradas **sin marca de agua** tras el pago exitoso.

### A3. Fotógrafo

- Usuario autenticado con **plan activo** (Freemium, Básico, Premium, Enterprise).
- Accede a un **panel personal** en el front-end donde puede:
  - Configurar su perfil.
  - Configurar su **marca de agua**.
  - Crear/editar/archivar **eventos**, **álbumes** y **fotos**.
  - Gestionar su contenido publicado.
- Comercializa sus fotos desde:
  - Su **perfil público**.
  - Las páginas de **evento** y **álbum**.

### A4. Administrador del Sistema

- Gestiona **categorías predefinidas** y sus fotos de portada.
- Configura **planes de fotógrafo** y parámetros globales:
  - Comisiones.
  - Tiempos de archivado y eliminación de fotos.
- Gestiona la **facturación de comisiones** a fotógrafos y seguimiento de deuda.
- Suspende y reactiva cuentas de fotógrafos morosos.

---

## 3. Suposiciones y Dependencias

- Se utilizan módulos base de Odoo:
  - **Website**
  - **e-Commerce**
  - **CRM**
  - **Facturación/Accounting** (para comisiones)
- Se integra **Mercado Pago** como pasarela de pago para:
  - Compras de fotos por parte de clientes.
  - Pago de comisiones por parte de fotógrafos.
- Las **categorías** de eventos son **predefinidas** (no las crea el fotógrafo).
- El almacenamiento y envío de fotos **sin marca de agua** se realiza de forma segura:
  - No deben ser accesibles públicamente por URL directa sin permisos.
- La **facturación de comisiones** a fotógrafos se realiza usando el módulo de facturación de Odoo (o similar), con pago también vía Mercado Pago.

---

## 4. Requisitos Funcionales (RF)

### 4.1 Categorías Predefinidas

**RF-01 – Lista de categorías predefinidas**

- **RF-01.01**: El sistema debe tener una lista de categorías predefinidas, entre ellas (lista de referencia, no exhaustiva):  
  `fútbol, futsal, running, vóley, tenis de playa, fiestas, básquet, congreso, handball, crossfit, ciclismo, automovilismo, tenis, airsoft, música, artes marciales, boxeo, caminata, concierto, e-sports, ferias, graduación, fut-voley, gimnasia artística, motocross, hipismo, hockey, yoga, jiu-jitsu, judo, karate, motociclismo, mountain bike, natación, pádel, patín, pilates, teatro, skate, surf, ping pong, capoeira, triatlón, powerlifting, entrenamiento, escalada, rugby, otros, fisicoculturismo, atletismo, religión, bautismo, casamiento, retratos, danza clásica, ensayos, badminton, buceo, escolar, canotaje, ajedrez, animales, productos, desfile de moda, desfiles, eventos sociales, viajes, carnaval, fútbol de playa, lucha libre, muay thai, paisajes, bowling, shows, BMX, paracaidismo, vuelo libre, poker, spinning.`

- **RF-01.02**: Cada categoría debe tener una **foto de portada** cargada previamente por el administrador.

- **RF-01.03**: Los fotógrafos **no pueden crear nuevas categorías**, solo seleccionar una existente para sus eventos.

---

### 4.2 Página de Inicio (Home)

**RF-10 – Vista de categorías en inicio**

- **RF-10.01**: La home debe mostrar un **preview de ~8 categorías** con su foto de portada y nombre.
- **RF-10.02**: Debe existir un botón **“Ver todas las categorías”** que redirige a la página de listado completo.

**RF-11 – Vista de eventos recientes en inicio**

- **RF-11.01**: La home debe mostrar un **preview de 16 eventos** publicados recientemente.
- **RF-11.02**: Cada tarjeta de evento debe mostrar:
  - Nombre del evento.
  - Foto de portada.
  - Fecha del evento.
  - Lugar del evento.
  - Nombre del fotógrafo.
- **RF-11.03**: Al hacer clic en la tarjeta, se redirige a la **página del evento**.

**RF-12 – Vista de fotógrafos en inicio**

- **RF-12.01**: La home debe mostrar un **preview de 16 fotógrafos**.
- **RF-12.02**: La tarjeta de cada fotógrafo incluye:
  - Foto del fotógrafo.
  - Descripción breve.
  - Plan actual (Freemium/Básico/Premium/Enterprise).
  - Cantidad de fotos subidas.
- **RF-12.03**: Botón **“Ver todos los fotógrafos”** que redirige al listado completo.
- **RF-12.04**: Posibilidad de **filtrar fotógrafos por nombre** (buscador).
- **RF-12.05**: Al hacer clic en la tarjeta, se abre el **perfil público** del fotógrafo con sus eventos.

---

### 4.3 Páginas de Navegación Pública

**RF-20 – Página de categorías**

- **RF-20.01**: Página pública con el listado de **todas las categorías**, mostrando foto de portada y nombre.
- **RF-20.02**: Al hacer clic en una categoría, se muestran los **eventos asociados**.

**RF-21 – Perfil público del fotógrafo**

- **RF-21.01**: Debe mostrar:
  - Nombre del fotógrafo.
  - Foto de perfil.
  - Descripción breve.
  - Plan actual.
  - Cantidad de fotos subidas.
- **RF-21.02**: Debe listar los eventos del fotógrafo:
  - Nombre del evento.
  - Foto de portada.
  - Fecha y lugar.
  - Categoría.
- **RF-21.03**: Al hacer clic en un evento, se abre la **página del evento**.

**RF-22 – Página de evento**

- **RF-22.01**: Muestra:
  - Nombre del evento.
  - Foto de portada.
  - Fecha y lugar.
  - Categoría del evento.
  - Fotógrafo.
- **RF-22.02**: Lista los **álbumes** del evento y, dentro de cada uno, las **fotos**.
- **RF-22.03**: El usuario puede navegar **álbum por álbum**.
- **RF-22.04**: Desde la página de evento/álbum:
  - Agregar fotos individuales al **carrito**.
  - Agregar **todas las fotos de un álbum** al carrito.

**RF-23 – Página de foto**

- **RF-23.01**: La vista individual muestra la foto con la **marca de agua aplicada**.
- **RF-23.02**: Permite **añadir la foto al carrito**.
- **RF-23.03**: Muestra el **precio** y datos básicos del producto/foto.

---

### 4.4 Gestión del Contenido por Fotógrafo (Front-End)

**RF-30 – Panel personal del fotógrafo**

- **RF-30.01**: Al iniciar sesión, si el usuario es fotógrafo (plan activo), ve un **panel personal** en el front-end.
- **RF-30.02**: Desde el panel accede a:
  - Configuración de perfil.
  - Configuración de marca de agua.
  - Mis eventos.
  - Mis álbumes (por evento).
  - Mis fotos.

**RF-31 – Configuración de marca de agua**

- **RF-31.01**: El fotógrafo puede **subir una imagen** de marca de agua desde su panel.
- **RF-31.02**: La marca de agua se aplica **automáticamente** sobre todas las fotos que suba ese fotógrafo.
- **RF-31.03**: La foto original sin marca de agua se conserva internamente para el **envío al comprador** tras la compra.

**RF-32 – Creación y gestión de eventos**

- **RF-32.01**: El fotógrafo puede **crear eventos** desde su panel.
- **RF-32.02**: El formulario de creación incluye:
  - Nombre del evento.
  - Fecha.
  - Lugar.
  - Foto de portada.
  - Categoría (de la lista predefinida; no editable por el fotógrafo).
- **RF-32.03**: El fotógrafo puede **editar y archivar** eventos desde su panel.

**RF-33 – Creación y gestión de álbumes**

- **RF-33.01**: Dentro de un evento, el fotógrafo puede crear **múltiples álbumes**.
- **RF-33.02**: Cada álbum tiene:
  - Nombre.
  - Descripción (opcional).
- **RF-33.03**: El fotógrafo puede listar, editar y eliminar álbumes (según la lógica de negocio y ventas asociadas).

**RF-34 – Subida masiva de fotos**

- **RF-34.01**: Dentro de un álbum, el fotógrafo puede **subir fotos masivamente**, mínimo 10 por lote.
- **RF-34.02**: La interfaz soporta **selección múltiple** e idealmente **drag & drop**.
- **RF-34.03**: Al subir cada foto, el sistema debe:
  - Guardar la imagen **original**.
  - Generar la versión con **marca de agua**.
  - Generar una **miniatura** para listados.
  - Asociar la foto al **álbum, evento y fotógrafo**.

---

### 4.5 Planes de Fotógrafo y Comisión

**RF-40 – Planes disponibles**

Deben existir 4 planes de fotógrafo:

| Plan       | Límite de fotos subidas | Comisión retenida | Precio mensual |
| ---------- | ------------------------ | ----------------- | -------------- |
| Freemium   | 30 fotos                 | 60%               | 0 USD          |
| Básico     | 50 fotos                 | 40%               | 15 USD         |
| Premium    | 150 fotos                | 25%               | 25 USD         |
| Enterprise | 400 fotos                | 10%               | 35 USD         |

- **RF-40.02**: El límite de fotos se cuenta por **cantidad de fotos subidas**, independientemente de si están publicadas, archivadas o no.
- **RF-40.03**: La comisión es el **porcentaje que retiene el sistema** sobre las ventas de fotos de ese fotógrafo.

**RF-41 – Selección de tipo de usuario y plan al registrarse**

- **RF-41.01**: En el registro de usuario, debe poder seleccionarse:
  - “¿Usuario tipo fotógrafo?” **Sí/No**.
- **RF-41.02**: Si marca “Sí”, debe elegir uno de los planes (Freemium/Básico/Premium/Enterprise).
- **RF-41.03**: Al confirmar el registro como fotógrafo con plan, se **desbloquea su panel** con todas las funcionalidades.
- **RF-41.04**: Si no elige plan (o indica que no es fotógrafo), queda como **usuario comprador** (sin panel de fotógrafo).

**RF-42 – Lógica de conteo de fotos por plan**

- **RF-42.01**: El sistema **impide subir nuevas fotos** si el fotógrafo alcanzó el máximo de su plan.
- **RF-42.02**: Ejemplo: Plan Básico (50 fotos) → 40 publicadas + 10 archivadas = 50 → no puede subir más.
- **RF-42.03**: Al **eliminar** una foto, se libera un “slot” y puede subir otra.
- **RF-42.04**: Archivado/publicación **no afectan el conteo**; solo la eliminación.
- **RF-42.05**: El panel del fotógrafo debe mostrar un **contador**:
  - Cantidad de fotos subidas.
  - Límite total del plan.

**RF-43 – Comisión y facturación al fotógrafo**

- **RF-43.01**: Por las ventas de fotos, el sistema calcula la **comisión** según el % del plan.
- **RF-43.02**: La comisión se **factura mensualmente** al fotógrafo.
- **RF-43.03**: Se puede definir un **umbral** (ej.: cada 5 fotos vendidas) para agrupar facturas.
- **RF-43.04**: Por cada período, se genera al menos **una factura** de comisión con el % aplicable.
- **RF-43.05**: La factura de comisión se paga por **Mercado Pago**.

**RF-44 – Manejo de deuda y suspensión de cuenta**

- **RF-44.01**: Si el fotógrafo **no paga** y acumula deuda > 1 mes, el sistema **suspende** su cuenta.
- **RF-44.02**: Fotógrafo suspendido:
  - No puede seguir comercializando fotos (no se deben poder comprar sus fotos desde el front).
- **RF-44.03**: La suscripción se **da de baja** (deja de ser fotógrafo activo; puede quedar solo como comprador).
- **RF-44.04**: Debe existir una lógica para **reactivar** la cuenta (por ejemplo, al regularizar pagos).

---

### 4.6 Venta de Fotos, Mercado Pago y Entrega

**RF-50 – Carrito y compra**

- **RF-50.01**: Fotos seleccionadas (individuales o masivamente) deben poder agregarse al **carrito estándar** de Odoo.
- **RF-50.02**: Opcionalmente, el usuario puede **combinar fotos de distintos fotógrafos** en una misma orden.
- **RF-50.03**: El **checkout** debe integrarse con **Mercado Pago** para procesar el pago.

**RF-51 – Integración con Mercado Pago**

- **RF-51.01**: Mercado Pago se usa como pasarela tanto para:
  - Compras de fotos.
  - Pago de facturas de comisión de fotógrafos.
- **RF-51.02**: Al confirmarse el pago exitoso, el pedido se marca como **pagado**.

**RF-52 – Envío automático de foto sin marca de agua**

- **RF-52.01**: Tras confirmar la venta (pago por Mercado Pago), el sistema envía por email la **foto original sin marca de agua** al comprador.
- **RF-52.02**: El email se envía a la dirección del cliente asociada al pedido (completada en el formulario previo al pago).
- **RF-52.03**: La foto sin marca de agua **no debe ser accesible públicamente** por URL directa sin control de permisos.

---

### 4.7 Ciclo de Vida de las Fotos (Publicación, Archivado, Eliminación)

**RF-60 – Publicación inicial**

- **RF-60.01**: Al subir una foto a un álbum, queda por defecto en estado **Publicada**, visible y disponible para venta.

**RF-61 – Archivado automático por falta de venta**

- **RF-61.01**: Si una foto no se vende en **X meses** (configurable), pasa a estado **Archivada** (no pública).
- **RF-61.02**: Una foto archivada no aparece en el perfil público del fotógrafo ni en páginas de evento/álbum.

**RF-62 – Republicación manual**

- **RF-62.01**: El fotógrafo puede **republicar** una foto archivada desde su panel.
- **RF-62.02**: Al republicar, la foto vuelve a **Publicada** por un nuevo período de X tiempo (configurable).

**RF-63 – Eliminación definitiva por inactividad**

- **RF-63.01**: Si tras un período adicional (ej.: otro mes) la foto no se republica, el sistema la **elimina**.
- **RF-63.02**: Los tiempos de archivado y eliminación son **configurables** por el administrador.
- **RF-63.03**: Al eliminar la foto, deja de contar para el **límite de fotos subidas**, liberando un slot.

**RF-64 – Exclusión en rankings de fotos republicadas**

- **RF-64.01**: Fotos republicadas no deben aparecer en secciones como:
  - Fotos destacadas.
  - Más vendidas.
  - Más vistas.
  - Más famosas.

---

### 4.8 CRM por Fotógrafo

**RF-70 – Oportunidades en CRM**

- **RF-70.01**: Cada compra de foto crea una **oportunidad** en el CRM del fotógrafo dueño de la foto.
- **RF-70.02**: La oportunidad se asocia al **cliente** y a la **venta** correspondiente.

**RF-71 – Oportunidad ganada**

- **RF-71.01**: Al confirmarse la venta (pago aprobado), la oportunidad se marca como **Ganada**.
- **RF-71.02**: El importe de la oportunidad refleja el valor de las fotos del fotógrafo vendidas en esa orden.

**RF-72 – CRM independiente por fotógrafo**

- **RF-72.01**: Cada fotógrafo debe tener su propio **pipeline de CRM** (o segmentación equivalente), de forma que sus oportunidades **no se mezclen** con las de otros fotógrafos.

---

## 5. Instalación (entorno Docker)

Este proyecto está pensado para ejecutarse en un entorno Docker usando:

- `docker compose` (archivo `compose.yaml` / `docker-compose.yml`)
- Una imagen personalizada de Odoo 18 definida en el `Dockerfile`
- Dependencias Python gestionadas en `requirements.txt`
- El módulo en `addons/fotoapp`

### 5.1. Prerrequisitos

Antes de empezar, necesitás tener instalado en tu máquina:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/) (en Windows/Mac viene integrado con Docker Desktop)
- Git (opcional, pero recomendado)

### 5.2. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO> fotoapp-odoo18
cd fotoapp-odoo18
