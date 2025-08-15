from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # İstehsalçı ölkə
    manufacturer_country_id = fields.Many2one(
        'res.country', 
        string='İstehsalçı Ölkə',
        help='Məhsulun istehsal edildiyi ölkə'
    )
    
    # İstehsalçı firma
    manufacturer_company = fields.Char(
        string='İstehsalçı Firma',
        help='Məhsulu istehsal edən firma/şirkət'
    )
    
    # Təsir edici ana maddə
    active_ingredient = fields.Char(
        string='Təsir Edici Ana Maddə',
        help='Məhsulun təsir edici ana maddələri (kimyəvi tərkib)'
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
