# -*- coding: utf-8 -*-

{
    'name': 'Kənd Təsərrüfatı İdarəetmə Sistemi',
    'version': '18.0.1.5.4',
    'category': 'Agriculture',
    'summary': 'Ferma sahələrinin, ağacların, əməliyyatların və xərclərin idarə edilməsi',
    'description': """
        Kənd Təsərrüfatı İdarəetmə Sistemi
        
        Bu modul aşağıdakı funksiyaları təmin edir:
        * Ferma sahələrinin idarə edilməsi
        * Ağac və parsel idarəetməsi  
        * Əməliyyatların (şumlama, əkin, sulama, gübrələmə, budama, yığım) izlənilməsi
        * İşçi və xərc idarəetməsi
        * Detallı xərc hesabatları və analitikaları
        * Satınalma və inventar idarəetməsi
    """,
    'author': 'Farm Management Team',
    'website': 'https://www.github.com/7aim',
    'images': [
        'static/description/icon.png',
    ],
    'depends': ['base', 'stock', 'product','purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/farm_data.xml',
        #'data/founder_demo_data.xml',
        'views/farm_field_wizard_views.xml',
        'views/farm_field_views.xml',
        'views/farm_parcel_views.xml',
        'views/farm_row_views.xml',
        'views/farm_tree_views.xml',
        'views/farm_variety_views.xml',
        'views/farm_disease_views.xml',
        'views/farm_pallet_views.xml',
        'views/farm_cooler_views.xml',
        'views/farm_operations_views.xml',
        'views/farm_worker_views.xml',
        'views/farm_expense_views.xml',
        'views/farm_cash_views.xml',
        'views/farm_meter_views.xml',
        'views/farm_expense_report_views.xml',
        'views/farm_communal_expense_views.xml',
        'views/farm_diesel_expense_views.xml',
        'views/farm_tractor_expense_views.xml',
        'views/farm_tractor_income_views.xml',
        'views/farm_material_expense_views.xml',
        "views/farm_resource_views.xml",
        'views/farm_document_views.xml',
        'views/farm_hotel_expense_views.xml',
        'views/farm_dashboard_wizard_views.xml',
        'views/product_template_views.xml',
        'views/purchase_order.xml',
        'views/farm_menu.xml',
    ],
    'web_icon': 'farm_agriculture_v2,static/description/icon.png',

    'installable': True,
    'auto_install': False,
    'application': True,
}