# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from datetime import datetime

class FarmExpenseReport(models.Model):
    _name = 'farm.expense.report'
    _description = 'Ümumi Xərc Hesabatı'
    _auto = False
    _order = 'date desc'

    name = fields.Char('Açıqlama', readonly=True)
    date = fields.Date('Tarix', readonly=True)
    amount = fields.Float('Məbləğ', readonly=True)
    expense_type = fields.Char('Xərc Növü', readonly=True)
    year = fields.Char('İl', readonly=True)
    month = fields.Char('Ay', readonly=True)
    quarter = fields.Char('Rüb', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                -- Kommunal Xərclər
                SELECT 
                    row_number() OVER () AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Kommunal' AS expense_type,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter
                FROM farm_communal_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Dizel Xərclər
                SELECT 
                    row_number() OVER () + 10000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Dizel' AS expense_type,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter
                FROM farm_diesel_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Traktor Xərclər
                SELECT 
                    row_number() OVER () + 20000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Traktor' AS expense_type,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter
                FROM farm_tractor_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Mal-Material Xərclər
                SELECT 
                    row_number() OVER () + 30000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Mal-material' AS expense_type,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter
                FROM farm_material_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Otel Xərclər
                SELECT 
                    row_number() OVER () + 40000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Otel' AS expense_type,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter
                FROM farm_hotel_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Maaş Ödənişləri
                SELECT 
                    row_number() OVER () + 50000 AS id,
                    'Maaş Ödənişi - ' || fw.name AS name,
                    fwp.payment_date AS date,
                    fwp.amount,
                    'Maaş' AS expense_type,
                    EXTRACT(year FROM fwp.payment_date)::text AS year,
                    EXTRACT(month FROM fwp.payment_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fwp.payment_date)::text AS quarter
                FROM farm_worker_payment fwp
                JOIN farm_worker fw ON fwp.worker_id = fw.id
                WHERE fwp.payment_date IS NOT NULL
                
                UNION ALL
                
                -- Əlavə Fəhlə Xərcləri (farm_additional_expense)
                SELECT 
                    row_number() OVER () + 60000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter
                FROM farm_additional_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Əməliyyatlardakı İşçi Xərcləri (Fəhlə kateqoriyasında)
                SELECT 
                    row_number() OVER () + 65000 AS id,
                    'Şumlama - ' || fw.name AS name,
                    fp.operation_date::date AS date,
                    fpw.amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM fp.operation_date)::text AS year,
                    EXTRACT(month FROM fp.operation_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fp.operation_date)::text AS quarter
                FROM farm_plowing_worker fpw
                JOIN farm_plowing fp ON fpw.plowing_id = fp.id
                JOIN farm_worker fw ON fpw.worker_id = fw.id
                WHERE fp.operation_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 66000 AS id,
                    'Əkin - ' || fw.name AS name,
                    fpl.planting_date::date AS date,
                    fplw.amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM fpl.planting_date)::text AS year,
                    EXTRACT(month FROM fpl.planting_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fpl.planting_date)::text AS quarter
                FROM farm_planting_worker fplw
                JOIN farm_planting fpl ON fplw.planting_id = fpl.id
                JOIN farm_worker fw ON fplw.worker_id = fw.id
                WHERE fpl.planting_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 67000 AS id,
                    'Sulama - ' || fw.name AS name,
                    fi.irrigation_date::date AS date,
                    fiw.amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM fi.irrigation_date)::text AS year,
                    EXTRACT(month FROM fi.irrigation_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fi.irrigation_date)::text AS quarter
                FROM farm_irrigation_worker fiw
                JOIN farm_irrigation fi ON fiw.irrigation_id = fi.id
                JOIN farm_worker fw ON fiw.worker_id = fw.id
                WHERE fi.irrigation_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 68000 AS id,
                    'Gübrələmə - ' || fw.name AS name,
                    ff.fertilizing_date::date AS date,
                    ffw.amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM ff.fertilizing_date)::text AS year,
                    EXTRACT(month FROM ff.fertilizing_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM ff.fertilizing_date)::text AS quarter
                FROM farm_fertilizing_worker ffw
                JOIN farm_fertilizing ff ON ffw.fertilizing_id = ff.id
                JOIN farm_worker fw ON ffw.worker_id = fw.id
                WHERE ff.fertilizing_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 69000 AS id,
                    'Dərmanlama - ' || fw.name AS name,
                    ft.treatment_date::date AS date,
                    ftw.amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM ft.treatment_date)::text AS year,
                    EXTRACT(month FROM ft.treatment_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM ft.treatment_date)::text AS quarter
                FROM farm_treatment_worker ftw
                JOIN farm_treatment ft ON ftw.treatment_id = ft.id
                JOIN farm_worker fw ON ftw.worker_id = fw.id
                WHERE ft.treatment_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 69500 AS id,
                    'Budama - ' || fw.name AS name,
                    fpr.pruning_date::date AS date,
                    fprw.amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM fpr.pruning_date)::text AS year,
                    EXTRACT(month FROM fpr.pruning_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fpr.pruning_date)::text AS quarter
                FROM farm_pruning_worker fprw
                JOIN farm_pruning fpr ON fprw.pruning_id = fpr.id
                JOIN farm_worker fw ON fprw.worker_id = fw.id
                WHERE fpr.pruning_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 69700 AS id,
                    'Yığım - ' || fw.name AS name,
                    fh.harvest_date::date AS date,
                    fhw.amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM fh.harvest_date)::text AS year,
                    EXTRACT(month FROM fh.harvest_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fh.harvest_date)::text AS quarter
                FROM farm_harvest_worker fhw
                JOIN farm_harvest fh ON fhw.harvest_id = fh.id
                JOIN farm_worker fw ON fhw.worker_id = fw.id
                WHERE fh.harvest_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 69800 AS id,
                    'Soyuducu - ' || fw.name AS name,
                    fcs.storage_date::date AS date,
                    fcsw.amount,
                    'Fəhlə' AS expense_type,
                    EXTRACT(year FROM fcs.storage_date)::text AS year,
                    EXTRACT(month FROM fcs.storage_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fcs.storage_date)::text AS quarter
                FROM farm_cold_storage_worker fcsw
                JOIN farm_cold_storage fcs ON fcsw.cold_storage_id = fcs.id
                JOIN farm_worker fw ON fcsw.worker_id = fw.id
                WHERE fcs.storage_date IS NOT NULL
                
                UNION ALL
                
                -- Satınalmalar
                SELECT 
                    row_number() OVER () + 70000 AS id,
                    'Satınalma - ' || po.name AS name,
                    po.date_order::date AS date,
                    po.amount_total,
                    'Satınalmalar' AS expense_type,
                    EXTRACT(year FROM po.date_order)::text AS year,
                    EXTRACT(month FROM po.date_order)::text AS month,
                    'Q' || EXTRACT(quarter FROM po.date_order)::text AS quarter
                FROM purchase_order po
                WHERE po.state IN ('purchase', 'done') 
                AND po.date_order IS NOT NULL
            )
        """ % self._table)

    @api.model
    def add_total_expense_to_cash(self):
        """Ümumi xərci kassaya əlavə edir"""
        # Bütün xərclərin ümumi məbləğini hesabla
        total_expenses = sum(self.search([]).mapped('amount'))
        
        if total_expenses > 0:
            # Kassaya məxaric əlavə et
            self.env['farm.cash.flow'].create({
                'name': f'Ümumi Xərclər - {fields.Date.today()}',
                'amount': total_expenses,
                'transaction_type': 'expense',
                'date': fields.Date.today(),
                'reference': 'total_expense_report',
                'note': f'Xərc hesabatından ümumi məbləğ: {total_expenses:.2f} AZN'
            })
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Uğurlu!',
                'message': f'Ümumi xərc ({total_expenses:.2f} AZN) kassaya əlavə edildi.',
                'sticky': False,
                'type': 'success'
            }
        }
