from odoo import models, fields

class FarmEquipment(models.Model):
    _name = 'farm.equipment'
    _description = 'Avadanlıq'

    name = fields.Char(string='Avadanlıq adı', required=True)
    category = fields.Selection([
        ('container', 'Konteyner ev'),
        ('irrigation', 'Suvarma dəsti'),
        ('generator', 'Generator'),
        ('pump', 'Nasos'),
        ('tank', 'Su çəni'),
        ('tractor', 'Traktor avadanlıqları'),
        ('plow', 'Şum aləti'),
        ('sprayer', 'Dərmanlama aparatı'),
        ('fertilizer', 'Gübrələmə sistemi'),
        ('solar', 'Günəş paneli və enerji sistemi'),
        ('fence', 'Hasar və qoruma sistemi'),
        ('warehouse', 'Anbar və soyuducu konteyner'),
        ('tools', 'Əl alətləri'),
        ('vehicle', 'Nəqliyyat vasitələri'),
        ('other', 'Digər'),
    ], string='Kateqoriya')
    purchase_date = fields.Date(string='Alınma tarixi')
    cost = fields.Float(string='Məbləğ (AZN)')
    payment_method = fields.Selection([
        ('cash', 'Nağd'),
        ('card', 'Kartla'),
    ], string='Ödəniş üsulu')
    notes = fields.Text(string='Qeydlər')
