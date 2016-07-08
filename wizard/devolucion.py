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

import time

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import logging

class pos_distefano_devolucion(osv.osv_memory):
    _name = 'pos_distefano.devolucion'
    _description = 'Devolucion'

    def _default_lineas(self, cr, uid, context=None):
        if not context:
            context = {}
        session = False
        order_obj = self.pool.get('pos.order')
        active_id = context and context.get('active_id', False)

        if active_id:
            order = order_obj.browse(cr, uid, active_id, context=context)
            lineas = []
            for l in order.lines:
                if l.devuelto:
                    raise osv.except_osv(_('Error'), _('Este pedido ya fue devuelto anteriormente, no puede ser devuelto dos veces.'))

                lineas.append({ 'linea': l.id, 'cantidad': l.qty })
            logging.warn(lineas)
            return lineas

        return False

    def devolver(self, cr, uid, ids, context=None):
        clone_list = []
        line_obj = self.pool.get('pos.order.line')
        order_obj = self.pool.get('pos.order')

        active_id = context and context.get('active_id', False)

        if active_id:
            for d in self.browse(cr, uid, ids, context=context):
                order = order_obj.browse(cr, uid, active_id, context=context)

                current_session_ids = self.pool.get('pos.session').search(cr, uid, [
                    ('state', '!=', 'closed'),
                    ('user_id', '=', uid)], context=context)
                if not current_session_ids:
                    raise osv.except_osv(_('Error!'), _('To return product(s), you need to open a session that will be used to register the refund.'))

                clone_id = order_obj.copy(cr, uid, order.id, {
                    'name': order.name + ' DEVOLUCION', # not used, name forced by create
                    'session_id': current_session_ids[0],
                    'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'pedido_original': order.id,
                    'lines': []
                }, context=context)
                clone_list.append(clone_id)

                for l in d.lineas:
                    if l.linea.devuelto:
                        raise osv.except_osv(_('Error'), _('Este pedido ya fue devuelto anteriormente, no puede ser devuelto dos veces.'))

                    if l.cantidad > l.linea.qty:
                        raise osv.except_osv(_('Error'), _('No se puede devolver mas de la cantidad original.'))

                    line_clone_id = line_obj.copy(cr, uid, l.linea.id, {
                        'order_id': clone_id,
                        'qty': -1 * l.cantidad
                    }, context=context)

        abs = {
            'name': _('Return Products'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': clone_list[0],
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        return abs

    _columns = {
        'lineas' : fields.one2many('pos_distefano.devolucion.linea', 'devolucion', 'Lineas'),
    }

    _defaults = {
        'lineas' : _default_lineas,
    }

class pos_distefano_devolucion_linea(osv.osv_memory):
    _name = 'pos_distefano.devolucion.linea'
    _description = 'Devolucion linea'

    _columns = {
        'devolucion' : fields.many2one('pos_distefano.devolucion', 'Devolucion', required=True, ondelete='cascade'),
        'linea' : fields.many2one('pos.order.line', 'Linea del pedido', required=True),
        'cantidad': fields.float('Cantidad', digits_compute=dp.get_precision('Product UoS')),
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
