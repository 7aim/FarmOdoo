from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class FarmMaterialExpense(models.Model):
    """Mal-Material Xərcləri"""
    _name = 'farm.material.expense'
    _description = 'Mal-Material Xərcləri'
    _order = 'expense_date desc'

    name = fields.Char('Xərc Adı', required=True, default='Mal-Material Xərci')
    expense_date = fields.Date('Tarix', required=True, default=fields.Date.today)
    field_id = fields.Many2one('farm.field', string='Sahə', required=True, ondelete='cascade')
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    
    # Material məlumatları
    material_type = fields.Selection([
        ('tools', 'Alətlər'),
        ('equipment', 'Avadanlıq'),
        ('supplies', 'Təchizat'),
        ('chemicals', 'Kimyəvi Maddələr'),
        ('seeds', 'Toxum'),
        ('fertilizer', 'Gübrə'),
        ('packaging', 'Qablaşdırma'),
        ('other', 'Digər')
    ], string='Material Növü', default='tools')

    supplier = fields.Many2one('res.partner', string='Təchizatçı', domain="[('category_id.name', '=', 'Təchizatçı')]", tracking=True)
    quantity = fields.Float('Miqdar')
    unit_price = fields.Float('Vahid Qiymət')
    
    # Hesabat üçün
    year = fields.Integer('İl', compute='_compute_date_fields', store=True)
    month = fields.Integer('Ay', compute='_compute_date_fields', store=True)
    quarter = fields.Integer('Rüb', compute='_compute_date_fields', store=True)

    @api.constrains('amount')
    def _check_balance_limit(self):
        """Xərc etməzdən əvvəl balansı yoxlayır"""
        for record in self:
            if record.amount > 0:
                cash_flow = self.env['farm.cash.flow']
                cash_flow.check_expense_balance(record.amount, 'farm.material.expense', record.id)
    
    @api.depends('expense_date')
    def _compute_date_fields(self):
        for record in self:
            if record.expense_date:
                date = fields.Date.from_string(record.expense_date)
                record.year = date.year
                record.month = date.month
                record.quarter = (date.month - 1) // 3 + 1
            else:
                record.year = 0
                record.month = 0
                record.quarter = 0
                
    @api.onchange('quantity', 'unit_price')
    def _onchange_amount_calculation(self):
        if self.quantity and self.unit_price:
            self.amount = self.quantity * self.unit_price
