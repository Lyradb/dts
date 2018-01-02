# -*- coding: utf-8 -*-
{
    'name': "Document Tracking System",

    'summary': """
        Document Tracking System (DTS)""",

    'description': """
        Long description of module's purpose
    """,

    'author': "DTS Solutions",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        'data/init_data.xml',
        'security/dts_document_security.xml',
        'security/ir.model.access.csv',
        'views/document_tracking_views.xml',
        'views/menuitems.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}