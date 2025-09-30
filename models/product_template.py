from odoo import models, fields, api


class ProductActiveIngredient(models.Model):
    _name = 'product.active.ingredient'
    _description = 'Təsir Edici Ana Maddələr'
    
    name = fields.Char('Ana Maddə Adı', required=True)
    chemical_formula = fields.Char('Kimyəvi Formula')
    description = fields.Text('Təsvir')
    
    # Əlaqəli məhsullar
    product_ids = fields.One2many('product.template', 'active_ingredient_id', string='Məhsullar')
    product_count = fields.Integer('Məhsul Sayı', compute='_compute_product_count')
    
    @api.depends('product_ids')
    def _compute_product_count(self):
        for record in self:
            record.product_count = len(record.product_ids)
    
    def action_view_products(self):
        """Ana maddə ilə əlaqəli məhsulları göstər"""
        return {
            'name': f'{self.name} - Məhsullar',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('active_ingredient_id', '=', self.id)],
            'target': 'current',
        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # İstehsalçı ölkə
    manufacturer_country_id = fields.Many2one(
        'res.country', 
        string='İstehsalçı Ölkə',
        help='Məhsulun istehsal edildiyi ölkə'
    )
    
    # İstehsalçı firma
    manufacturer_company = fields.Many2one(
        'res.partner',
        string='İstehsalçı Firma',
        help='Məhsulu istehsal edən firma/şirkət'
    )
    
    # Təsir edici ana maddə
    active_ingredient_id = fields.Many2one(
        'product.active.ingredient',
        string='Təsir Edici Ana Maddə',
        help='Məhsulun təsir edici ana maddəsi'
    )
    active_ingredient = fields.Char(
        string='Təsir Edici Ana Maddə (Köhnə)',
        help='Köhnə məlumat - yeni Ana Maddə əlaqəsini istifadə edin'
    )
    
    # Əlavə məlumat sahələri (ixtiyari)
    concentration = fields.Char(
        string='Konsentrasiya',
        help='Ana maddənin konsentrasiyası (məs: 20%, 50ml/l)'
    )
    
    registration_number = fields.Char(
        string='Qeydiyyat Nömrəsi',
        help='Dövlət qeydiyyat nömrəsi (pestisid, gübrə və s.)'
    )
    
    expiry_months = fields.Integer(
        string='Saxlama Müddəti (ay)',
        default=24,
        help='Məhsulun maksimum saxlama müddəti aylarda'
    )
    
    storage_conditions = fields.Text(
        string='Saxlama Şəraiti',
        help='Məhsulun saxlanma şərtləri (temperatur, rütubət və s.)'
    )
    
    def name_get(self):
        """Məhsul adında istehsalçı məlumatını göstər"""
        result = []
        for record in self:
            name = record.name
            if record.manufacturer_company:
                name = f"{name} ({record.manufacturer_company})"
            result.append((record.id, name))
        return result


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    def name_get(self):
        """Məhsul variantında da istehsalçı məlumatını göstər"""
        result = []
        for record in self:
            name = record.display_name
            if record.manufacturer_company:
                name = f"{name} ({record.manufacturer_company})"
            result.append((record.id, name))
        return result
