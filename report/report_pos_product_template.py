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

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.sql import drop_view_if_exists

class report_pos_product_template(osv.osv):
    _name = "distefano.report_pos_product_template"
    _description = "Analisis de ventas por producto"
    _auto = False
    _rec_name = 'product_template_id'

    _columns = {
        'qty': fields.float('Cantidad', readonly=True),
        'location_id': fields.many2one('stock.location', 'Ubicacion', readonly=True),
        'product_template_id': fields.many2one('product.template', 'Producto', readonly=True),
        'talla_id': fields.many2one('product.attribute.value', 'Talla', readonly=True),
        'color_id': fields.many2one('product.attribute.value', 'Color', readonly=True),
        'active': fields.boolean('Activo'),
        'date': fields.datetime('Fecha pedido', readonly=True),
        'partner_id':fields.many2one('res.partner', 'Empresa', readonly=True),
        'product_id':fields.many2one('product.product', 'Producto', readonly=True),
        'state': fields.selection([('draft', 'New'), ('paid', 'Closed'), ('done', 'Synchronized'), ('invoiced', 'Invoiced'), ('cancel', 'Cancelled')],
                                  'Estado'),
        'user_id':fields.many2one('res.users', 'Comercial', readonly=True),
        'price_total':fields.float('Precio Total', readonly=True),
        'total_discount':fields.float('Descuento total',readonly=True),
        'average_price': fields.float('Average Price',readonly=True,group_operator="avg"),
        'company_id':fields.many2one('res.company', 'Compañia', readonly=True),
        'nbr':fields.integer('# of Lines', readonly=True),  # TDE FIXME master: rename into nbr_lines
        'product_qty':fields.integer('Cantidad del producto', readonly=True),
        'journal_id': fields.many2one('account.journal' ,'Diario'),
        'delay_validation': fields.integer('Delay Validation'),
        'product_categ_id': fields.many2one('product.category','Categoría de producto', readonly=True),

    }
    _order = 'date desc'


    def init(self, cr):
        drop_view_if_exists(cr, 'distefano_report_pos_product_template')
        cr.execute("""
            create or replace view distefano_report_pos_product_template as (
            select
                min(l.id) as id,
                sum(l.qty) as qty,
                count(*) as nbr,
                s.date_order as date,
                sum(l.qty * u.factor) as product_qty,
                sum(l.qty * l.price_unit) as price_total,
                sum((l.qty * l.price_unit) * (l.discount / 100)) as total_discount,
                (sum(l.qty*l.price_unit)/sum(l.qty * u.factor))::decimal as average_price,
                sum(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') as int)) as delay_validation,
                s.partner_id as partner_id,
                s.state as state,
                s.user_id as user_id,
                s.location_id as location_id,
                s.company_id as company_id,
                s.sale_journal as journal_id,
                l.product_id as product_id,
                pt.categ_id as product_categ_id,
                p.product_tmpl_id as product_template_id,
                p.active as active,
                vpr1.att_id as color_id,
                vpr2.att_id as talla_id
            from
                pos_order_line l join product_product p on (l.product_id = p.id)
                join pos_order s on (s.id=l.order_id)
                left join product_template pt on (pt.id=p.product_tmpl_id)
                left join product_uom u on (u.id=pt.uom_id)
                join product_attribute_value_product_product_rel vpr1 on(p.id = vpr1.prod_id)
                join product_attribute_value v1 on(vpr1.att_id = v1.id and v1.attribute_id = 1)
                join product_attribute_value_product_product_rel vpr2 on(p.id = vpr2.prod_id)
                join product_attribute_value v2 on(vpr2.att_id = v2.id and v2.attribute_id = 2)
            group by product_template_id, color_id, talla_id,
                    s.date_order, s.partner_id,s.state, pt.categ_id,
                    s.user_id,s.location_id,s.company_id,s.sale_journal,l.product_id,s.create_date,p.active
            having
                    sum(l.qty * u.factor) != 0  )""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
