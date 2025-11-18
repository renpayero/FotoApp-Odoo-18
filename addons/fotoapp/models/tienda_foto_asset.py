import base64
import hashlib
import logging
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from PIL import Image, ImageDraw, ImageFont

_logger = logging.getLogger(__name__)


class TiendaFotoAsset(models.Model):
    _name = 'tienda.foto.asset'
    _description = 'Activos de fotos'
    _order = 'sequence, id desc'

    evento_id = fields.Many2one(
        comodel_name='tienda.foto.evento',
        string='Evento',
        required=True
    )
    photographer_id = fields.Many2one(
        'res.partner',
        string='Fotógrafo',
        related='evento_id.photographer_id',
        store=True,
        readonly=True
    )
    numero_dorsal = fields.Char(string='Número de Dorsal')
    sequence = fields.Integer(string='Secuencia', default=10)
    imagen_original = fields.Image(string='Imagen Original', required=True, attachment=True)
    imagen_watermark = fields.Image(string='Imagen con Marca de Agua', attachment=True)
    precio = fields.Monetary(string='Precio', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
    publicada = fields.Boolean(string='Publicada', default=False)
    website_published = fields.Boolean(string='Visible en web', default=False)
    checksum = fields.Char(string='Checksum', readonly=True)
    download_token = fields.Char(string='Token de descarga')
    batch_id = fields.Char(string='Lote de subida')

    def _compute_checksum(self, b64_image): 
        # Sirve para detectar duplicados o verificar integridad.
        # Convierte el binario base64 a bytes, calcula hashlib.sha256, guarda el resultado en el campo checksum.
        if not b64_image: #si viene vacío
            return False
        raw = base64.b64decode(b64_image)
        return hashlib.sha256(raw).hexdigest()
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            image_b64 = vals.get('imagen_original')
            if not image_b64:
                continue
            checksum = self._compute_checksum(image_b64)
            if checksum:
                vals['checksum'] = checksum
            self._generate_watermark(vals)
        return super().create(vals_list)
    
    def _generate_watermark(self, vals):
        image_b64 = vals.get('imagen_original')
        if not image_b64:
            return vals
        try:
            raw = base64.b64decode(image_b64)
            image = Image.open(BytesIO(raw)).convert("RGBA") #abre la imagen y la convierte apra poder trabajarla.
        except Exception as exc:
            _logger.warning("No se pudo generar la marca de agua: %s", exc)
            return vals
    
        watermark = Image.new("RGBA", image.size)
        overlay_added = self._apply_partner_watermark(image, watermark, vals)
        if not overlay_added:
            draw = ImageDraw.Draw(watermark)
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except OSError:
                font = ImageFont.load_default()
            draw.text((30, 30), "FotoApp", fill=(255, 255, 255, 128), font=font)

        combined = Image.alpha_composite(image, watermark)
        buf = BytesIO() #crea un buffer en memoria para guardar la imagen resultante
        combined.convert("RGB").save(buf, format="JPEG", quality=85)
        vals['imagen_watermark'] = base64.b64encode(buf.getvalue())
        return vals

    def _apply_partner_watermark(self, base_image, watermark_layer, vals):
        partner = self._get_photographer(vals)
        if not partner or not partner.watermark_image:
            return False
        try:
            partner_img = Image.open(BytesIO(base64.b64decode(partner.watermark_image))).convert("RGBA")
        except Exception as exc:
            _logger.warning('Marca de agua inválida para %s: %s', partner.name, exc)
            return False

        scale = min(max(partner.watermark_scale or 0.3, 0.05), 1.0)
        opacity = min(max(partner.watermark_opacity or 60, 0), 100) / 100.0
        target_width = max(int(base_image.width * scale), 1)
        ratio = target_width / float(partner_img.width)
        target_height = max(int(partner_img.height * ratio), 1)
        partner_img = partner_img.resize((target_width, target_height), Image.LANCZOS)

        if partner_img.mode != 'RGBA':
            partner_img = partner_img.convert('RGBA')
        alpha = partner_img.split()[3].point(lambda p: int(p * opacity))
        partner_img.putalpha(alpha)

        margin = 40
        position = (
            max(base_image.width - partner_img.width - margin, margin),
            max(base_image.height - partner_img.height - margin, margin)
        )
        watermark_layer.alpha_composite(partner_img, dest=position)
        return True

    def _get_photographer(self, vals):
        if vals.get('photographer_id'):
            return self.env['res.partner'].browse(vals['photographer_id'])
        event_id = vals.get('evento_id')
        if not event_id:
            return None
        event = self.env['tienda.foto.evento'].browse(event_id)
        return event.photographer_id
    
    def write(self, vals):
        if 'imagen_original' in vals:
            vals = self._generate_watermark(vals)
            checksum = self._compute_checksum(vals['imagen_original'])
            if checksum:
                vals['checksum'] = checksum
        return super().write(vals)

    @api.constrains('precio')
    def _check_precio(self):
        for record in self:
            if record.precio <= 0:
                raise ValidationError(_('El precio debe ser mayor a cero.'))
    

