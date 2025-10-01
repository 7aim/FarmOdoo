from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class FarmFutureExpense(models.Model):
    """Gələcək Dövrün Xərci"""
    _name = 'farm.future.expense'
    _description = 'Gələcək Dövrün Xərci'
    _order = 'contract_date desc'

    name = fields.Char('Müqavilə Adı', required=True)
    contract_number = fields.Char('Müqavilə Nömrəsi', copy=False, readonly=True, default='/')
    
    # Əsas vəsait əlaqəsi
    asset_id = fields.Many2one('farm.resource', string='Əsas Vəsait', required=True)
    asset_name = fields.Char('Vəsait Adı', related='asset_id.name', readonly=True)
    asset_type = fields.Selection(related='asset_id.asset_type', readonly=True)
    
    # Maliyyə məlumatları
    total_price = fields.Float('Ümumi Qiymət', required=True)
    initial_payment = fields.Float('İlkin Ödəniş', default=0.0)
    subsidy_amount = fields.Float('Subsidiya Məbləği', default=0.0)
    original_debt = fields.Float('Orijinal Borc', compute='_compute_original_debt', store=True)
    remaining_debt = fields.Float('Qalan Borc', compute='_compute_remaining_debt', store=True)
    
    # Taksit məlumatları
    installment_months = fields.Integer('Taksit Müddəti (ay)', required=True, default=12)
    monthly_payment = fields.Float('Aylıq Ödəniş', compute='_compute_monthly_payment', store=True)
    annual_payment = fields.Float('İllik Ödəniş', compute='_compute_annual_payment', store=True)
    
    # Müqavilə məlumatları
    contract_date = fields.Date('Müqavilə Tarixi', required=True, default=fields.Date.today)
    first_payment_date = fields.Date('İlk Taksit Tarixi', required=True)
    last_payment_date = fields.Date('Son Taksit Tarixi', compute='_compute_last_payment_date', store=True)
    
    # Status
    status = fields.Selection([
        ('active', 'Aktiv'),
        ('completed', 'Tamamlanmış'),
        ('cancelled', 'Ləğv edilmiş')
    ], string='Status', default='active', required=True)
    
    # Təchizatçı və bank
    supplier_id = fields.Many2one('res.partner', string='Təchizatçı',
                                  domain="[('financial_category', 'in', ['creditor', 'both'])]")
    bank_id = fields.Many2one('res.partner', string='Bank/Lizinq Şirkəti')
    
    # Faiz məlumatları
    interest_rate = fields.Float('İllik Faiz Dərəcəsi (%)', default=0.0)
    total_interest = fields.Float('Ümumi Faiz', compute='_compute_total_interest', store=True)
    
    # Ödəniş cədvəli
    payment_line_ids = fields.One2many('farm.future.expense.line', 'expense_id', string='Ödəniş Cədvəli')
    paid_installments = fields.Integer('Ödənilmiş Taksitlər', compute='_compute_payment_stats')
    remaining_installments = fields.Integer('Qalan Taksitlər', compute='_compute_payment_stats')
    paid_amount = fields.Float('Ödənilmiş Məbləğ', compute='_compute_payment_stats')
    remaining_amount = fields.Float('Qalan Məbləğ', compute='_compute_payment_stats')
    
    # Qeydlər
    notes = fields.Text('Qeydlər')
    
    @api.model
    def create(self, vals):
        if vals.get('contract_number', '/') == '/':
            vals['contract_number'] = self.env['ir.sequence'].next_by_code('farm.future.expense') or '/'
        return super(FarmFutureExpense, self).create(vals)
    
    @api.depends('total_price', 'initial_payment', 'subsidy_amount')
    def _compute_original_debt(self):
        for record in self:
            record.original_debt = record.total_price - record.initial_payment - record.subsidy_amount
    
    @api.depends('original_debt', 'payment_line_ids.is_paid', 'payment_line_ids.amount')
    def _compute_remaining_debt(self):
        for record in self:
            paid_amount = sum(record.payment_line_ids.filtered('is_paid').mapped('amount'))
            record.remaining_debt = record.original_debt - paid_amount
    
    @api.depends('original_debt', 'installment_months', 'interest_rate')
    def _compute_monthly_payment(self):
        for record in self:
            if record.installment_months > 0:
                if record.interest_rate > 0:
                    # Faizli ödəniş hesablaması
                    monthly_rate = record.interest_rate / 100 / 12
                    factor = (1 + monthly_rate) ** record.installment_months
                    record.monthly_payment = record.original_debt * (monthly_rate * factor) / (factor - 1)
                else:
                    # Faizsiz ödəniş
                    record.monthly_payment = record.original_debt / record.installment_months
            else:
                record.monthly_payment = 0.0
    
    @api.depends('monthly_payment')
    def _compute_annual_payment(self):
        for record in self:
            record.annual_payment = record.monthly_payment * 12
    
    @api.depends('first_payment_date', 'installment_months')
    def _compute_last_payment_date(self):
        for record in self:
            if record.first_payment_date and record.installment_months:
                record.last_payment_date = record.first_payment_date + relativedelta(months=record.installment_months-1)
            else:
                record.last_payment_date = False
    
    @api.depends('monthly_payment', 'installment_months', 'original_debt')
    def _compute_total_interest(self):
        for record in self:
            total_payment = record.monthly_payment * record.installment_months
            record.total_interest = total_payment - record.original_debt
    
    @api.depends('payment_line_ids.is_paid', 'payment_line_ids.amount')
    def _compute_payment_stats(self):
        for record in self:
            paid_lines = record.payment_line_ids.filtered('is_paid')
            record.paid_installments = len(paid_lines)
            record.remaining_installments = len(record.payment_line_ids) - record.paid_installments
            record.paid_amount = sum(paid_lines.mapped('amount'))
            record.remaining_amount = sum(record.payment_line_ids.filtered(lambda l: not l.is_paid).mapped('amount'))
    
    @api.constrains('total_price', 'initial_payment', 'subsidy_amount')
    def _check_amounts(self):
        for record in self:
            if record.total_price <= 0:
                raise ValidationError('Ümumi qiymət müsbət olmalıdır!')
            if record.initial_payment < 0:
                raise ValidationError('İlkin ödəniş mənfi ola bilməz!')
            if record.subsidy_amount < 0:
                raise ValidationError('Subsidiya məbləği mənfi ola bilməz!')
            if (record.initial_payment + record.subsidy_amount) > record.total_price:
                raise ValidationError('İlkin ödəniş və subsidiya ümumi qiymətdən çox ola bilməz!')
    
    @api.constrains('installment_months')
    def _check_installment_months(self):
        for record in self:
            if record.installment_months <= 0:
                raise ValidationError('Taksit müddəti müsbət olmalıdır!')
    
    def generate_payment_schedule(self):
        """Ödəniş cədvəli yaradır"""
        self.payment_line_ids.unlink()
        
        payment_date = self.first_payment_date
        for month in range(1, self.installment_months + 1):
            self.env['farm.future.expense.line'].create({
                'expense_id': self.id,
                'installment_number': month,
                'payment_date': payment_date,
                'amount': self.monthly_payment,
                'is_paid': False
            })
            payment_date = payment_date + relativedelta(months=1)
    
    def action_complete(self):
        """Müqaviləni tamamlanmış kimi qeyd et"""
        self.write({'status': 'completed'})
    
    def action_cancel(self):
        """Müqaviləni ləğv et"""
        self.write({'status': 'cancelled'})


class FarmFutureExpenseLine(models.Model):
    """Gələcək Dövrün Xərci Sətiri"""
    _name = 'farm.future.expense.line'
    _description = 'Ödəniş Cədvəli Sətiri'
    _order = 'payment_date'

    expense_id = fields.Many2one('farm.future.expense', string='Gələcək Xərc', ondelete='cascade', required=True)
    installment_number = fields.Integer('Taksit Nömrəsi', required=True)
    payment_date = fields.Date('Ödəniş Tarixi', required=True)
    amount = fields.Float('Məbləğ', required=True)
    is_paid = fields.Boolean('Ödənilib', default=False)
    payment_date_actual = fields.Date('Faktiki Ödəniş Tarixi')
    notes = fields.Char('Qeyd')
    remaining_amount = fields.Float('Qalan Məbləğ', compute='_compute_remaining_amount', store=True)
    
    @api.depends('expense_id.remaining_debt', 'installment_number', 'expense_id.payment_line_ids.is_paid')
    def _compute_remaining_amount(self):
        """Bu taksitdən sonra qalan məbləği hesabla"""
        for line in self:
            if line.expense_id:
                # Bu taksitdən sonrakı ödənilməmiş taksitlərin sayı
                remaining_installments = line.expense_id.payment_line_ids.filtered(
                    lambda l: l.installment_number >= line.installment_number and not l.is_paid
                )
                line.remaining_amount = len(remaining_installments) * line.expense_id.monthly_payment
            else:
                line.remaining_amount = 0.0
    
    def action_mark_paid(self):
        """Ödənilmiş kimi qeyd et"""
        self.write({
            'is_paid': True,
            'payment_date_actual': fields.Date.today()
        })
        # Digər sətirlərin remaining_amount-ını yenilə
        self.expense_id.payment_line_ids._compute_remaining_amount()
    
    def action_mark_unpaid(self):
        """Ödənilməmiş kimi qeyd et"""
        self.write({
            'is_paid': False,
            'payment_date_actual': False
        })
        # Digər sətirlərin remaining_amount-ını yenilə
        self.expense_id.payment_line_ids._compute_remaining_amount()