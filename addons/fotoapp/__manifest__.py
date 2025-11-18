# -*- coding: utf-8 -*-
{
    'name': "fotoapp",

    'summary': "Aplicación de gestión y venta de fotos y álbumes",

    'description': "Gestion y venta de fotos y álbumes a través de una aplicación integrada con Odoo.",

    'author': "HC Sinergia",
    'website': "https://hcsinergia.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'website',
        'website_sale',
        'portal',
        'mail',
        'crm',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}

