
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Point of Sale Distefano',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Cambios para el manejo en Distefano ',
    'description': """

=======================

Cambios para el manejo en Distefano

""",
    'author': 'Rodrigo Fernandez',
    'depends': ['point_of_sale'],
    'data': [
        'point_of_sale_view.xml',
        'user_view.xml',
        'reports.xml',
        'views/templates.xml',
        'views/cierre.xml',
        'views/report_receipt.xml',
        'report/report_pos_product_template_view.xml',
        'wizard/devolucion.xml',
        'wizard/anulacion_devolucion.xml',
    ],
    'installable': True,
    'website': 'http://solucionesprisma.com',
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
