from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Kreditor/Debitor kateqoriyası
    financial_category = fields.Selection([
        ('creditor', 'Kreditor (Podratçı/Satıcı)'),
        ('debitor', 'Debitor (Alıcı/Sifarişçi)'),
        ('both', 'Həm Kreditor həm Debitor'),
        ('other', 'Digər')
    ], string='Maliyyə Kateqoriyası', help='Kontaktın maliyyə əlaqələri')
    
    # Əlavə sahələr kreditorlar üçün
    is_supplier = fields.Boolean('Təchizatçıdır', compute='_compute_financial_flags', store=True)
    is_contractor = fields.Boolean('Podratçıdır', compute='_compute_financial_flags', store=True)
    
    # Əlavə sahələr debitorlar üçün  
    is_customer = fields.Boolean('Müştəridir', compute='_compute_financial_flags', store=True)
    is_client = fields.Boolean('Sifarişçidir', compute='_compute_financial_flags', store=True)
    
    # Əlavə məlumatlar
    credit_limit = fields.Float('Kredit Limiti', help='Maksimum borc məbləği')
    payment_terms = fields.Text('Ödəniş Şərtləri', help='Ödəniş şərtləri və müddətləri')
    
    @api.depends('financial_category')
    def _compute_financial_flags(self):
        """Maliyyə kateqoriyasına əsasən boolean sahələri təyin et"""
        for partner in self:
            if partner.financial_category == 'creditor':
                partner.is_supplier = True
                partner.is_contractor = True
                partner.is_customer = False
                partner.is_client = False
            elif partner.financial_category == 'debitor':
                partner.is_supplier = False
                partner.is_contractor = False
                partner.is_customer = True
                partner.is_client = True
            elif partner.financial_category == 'both':
                partner.is_supplier = True
                partner.is_contractor = True
                partner.is_customer = True
                partner.is_client = True
            else:
                partner.is_supplier = False
                partner.is_contractor = False
                partner.is_customer = False
                partner.is_client = False
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Axtarışda maliyyə kateqoriyasını da daxil et"""
        if args is None:
            args = []
        
        # Əgər maliyyə kateqoriyası ilə axtarış edilsə
        domain = args[:]
        if name:
            domain = ['|', ('name', operator, name), ('financial_category', operator, name)] + domain
            
        return super(ResPartner, self).name_search(name, domain, operator, limit)