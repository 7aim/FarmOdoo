from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmWorker(models.Model):
    """İşçilər"""
    _name = 'farm.worker'
    _description = 'İşçilər'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('İşçi Adı', required=True)
    employee_code = fields.Char('İşçi Kodu', required=True)
    field_id = fields.Many2one('farm.field', string='Əsas İş Sahəsi', ondelete='set null')
    phone = fields.Char('Telefon')
    email = fields.Char('Email')
    address = fields.Text('Ünvan')

    # Status və məlumatlar
    active = fields.Boolean('Aktiv', default=True)
    hire_date = fields.Date('İşə Başlama Tarixi', default=fields.Date.today)
    salary = fields.Float('Maaş', required=True)

    # Hesablanmış sahələr
    total_operations = fields.Integer('Ümumi Əməliyyat Sayı', compute='_compute_statistics', store=True)
    total_earned = fields.Float('Əməliyyat Qazancı', compute='_compute_statistics', store=True)
    total_paid = fields.Float('Ümumi Ödəniş', compute='_compute_total_paid', store=True)
    balance = fields.Float('Balans', compute='_compute_balance', store=True)
    
    # Əməliyyat xətləri
    plowing_line_ids = fields.One2many('farm.plowing.worker', 'worker_id', string='Şumlama Əməliyyatları')
    planting_line_ids = fields.One2many('farm.planting.worker', 'worker_id', string='Əkin Əməliyyatları')
    irrigation_line_ids = fields.One2many('farm.irrigation.worker', 'worker_id', string='Sulama Əməliyyatları')
    fertilizing_line_ids = fields.One2many('farm.fertilizing.worker', 'worker_id', string='Gübrələmə Əməliyyatları')
    treatment_line_ids = fields.One2many('farm.treatment.worker', 'worker_id', string='Dərmanlama Əməliyyatları')
    pruning_line_ids = fields.One2many('farm.pruning.worker', 'worker_id', string='Budama Əməliyyatları')
    harvest_line_ids = fields.One2many('farm.harvest.worker', 'worker_id', string='Yığım Əməliyyatları')
    cold_storage_line_ids = fields.One2many('farm.cold.storage.worker', 'worker_id', string='Soyuducu Əməliyyatları')
    
    # Ödənişlər
    payment_line_ids = fields.One2many('farm.worker.payment', 'worker_id', string='Ödənişlər')

    @api.depends('plowing_line_ids', 'planting_line_ids', 'irrigation_line_ids', 
                 'fertilizing_line_ids', 'treatment_line_ids', 'pruning_line_ids',
                 'harvest_line_ids', 'cold_storage_line_ids')
    def _compute_statistics(self):
        for worker in self:
            # Hər model üçün ayrı-ayrı hesabla
            total_operations = (len(worker.plowing_line_ids) + len(worker.planting_line_ids) + 
                              len(worker.irrigation_line_ids) + len(worker.fertilizing_line_ids) +
                              len(worker.treatment_line_ids) + len(worker.pruning_line_ids) +
                              len(worker.harvest_line_ids) + len(worker.cold_storage_line_ids))
            
            total_earned = (sum(line.amount for line in worker.plowing_line_ids) +
                           sum(line.amount for line in worker.planting_line_ids) +
                           sum(line.amount for line in worker.irrigation_line_ids) +
                           sum(line.amount for line in worker.fertilizing_line_ids) +
                           sum(line.amount for line in worker.treatment_line_ids) +
                           sum(line.amount for line in worker.pruning_line_ids) +
                           sum(line.amount for line in worker.harvest_line_ids) +
                           sum(line.amount for line in worker.cold_storage_line_ids))
            
            worker.total_operations = total_operations
            worker.total_earned = total_earned

    @api.depends('payment_line_ids.amount')
    def _compute_total_paid(self):
        for worker in self:
            worker.total_paid = sum(payment.amount for payment in worker.payment_line_ids)

    @api.depends('total_earned', 'total_paid')
    def _compute_balance(self):
        for worker in self:
            worker.balance = worker.total_earned + worker.total_paid

    @api.constrains('employee_code')
    def _check_unique_code(self):
        for worker in self:
            if self.search_count([('employee_code', '=', worker.employee_code), ('id', '!=', worker.id)]) > 0:
                raise ValidationError('İşçi kodu unikal olmalıdır!')

    def action_view_payments(self):
        """Ödənişlər səhifəsini aç"""
        return {
            'name': 'İşçi Ödənişləri',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'farm.worker.payment',
            'domain': [('worker_id', '=', self.id)],
            'context': {'default_worker_id': self.id}
        }

class FarmWorkerPayment(models.Model):
    """İşçi Ödənişləri"""
    _name = 'farm.worker.payment'
    _description = 'İşçi Ödənişləri'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc'

    worker_id = fields.Many2one('farm.worker', string='İşçi', required=True, ondelete='cascade')
    payment_date = fields.Date('Ödəniş Tarixi', required=True, default=fields.Date.today)
    amount = fields.Float('Məbləğ', required=True)
    payment_type = fields.Selection([
        ('salary', 'Maaş'),
        ('daily', 'Günlük'),
        ('bonus', 'Bonus'),
        ('advance', 'Avans'),
        ('other', 'Digər')
    ], string='Ödəniş Növü', required=True, default='salary')
    description = fields.Text('Açıqlama')
    reference = fields.Char('İstinad')

    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError('Ödəniş məbləği müsbət olmalıdır!')
