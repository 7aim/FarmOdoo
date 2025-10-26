from odoo import models, fields, api

class FarmRootstock(models.Model):
    _name = 'farm.rootstock'
    _description = 'Çalaqaltılar'
    
    name = fields.Char('Çalaqaltı Adı', required=True)
    description = fields.Text('Təsvir')

class FarmSort(models.Model):
    _name = 'farm.sort'
    _description = 'Bitki Sortları'
    
    name = fields.Char('Sort Adı', required=True)
    description = fields.Text('Təsvir')

class FarmVariety(models.Model):
    _name = 'farm.variety'
    _description = 'Bitkilər'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fruit_type, name'

    name = fields.Char('Bitki Adı')
    code = fields.Char('Bitki Kodu', copy=False, readonly=True)

    # Cins
    fruit_species = fields.Char(string='Cins', required=True)

    # Növ
    fruit_type = fields.Char(string='Növ', required=True)

    name_az = fields.Char('Bitki Adı (Azerbaycanca)')
    # Sort
    variety_name = fields.Many2many('farm.sort', string='Sortlar')

    # Çalaqaltı
    rootstock = fields.Many2one('farm.rootstock', string='Çalaqaltı')

    # Xüsusiyyətlər
    maturity_period = fields.Selection([
        ('early', 'Erkən'),
        ('medium', 'Orta'),
        ('late', 'Gec')
    ], string='Yetişmə Dövrü')

    harvest_season = fields.Selection([
        ('spring', 'Yaz'),
        ('summer', 'Yay'),
        ('autumn', 'Payız'),
        ('winter', 'Qış')
    ], string='Məhsul Mövsümü')

    # Ağac məlumatları ilə əlaqə
    tree_ids = fields.One2many('farm.tree', 'variety_id', string='Ağaclar')
    tree_count = fields.Integer('Ağac Sayı', compute='_compute_tree_count')

    @api.depends('tree_ids')
    def _compute_tree_count(self):
        for record in self:
            record.tree_count = len(record.tree_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                # Sort kodu V001, V002, V003... formatında generasiya et
                last_variety = self.search([('code', 'like', 'V%')], order='code desc', limit=1)
                if last_variety and last_variety.code:
                    try:
                        number = int(last_variety.code[1:]) + 1
                        vals['code'] = f'V{number:03d}'
                    except ValueError:
                        vals['code'] = 'V001'
                else:
                    vals['code'] = 'V001'

                # Default ad ver
                if not vals.get('name'):
                    vals['name'] = vals['code']
        return super().create(vals_list)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Bitki kodu unikal olmalıdır!'),
    ]
