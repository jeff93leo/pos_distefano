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

class pos_distefano_anulacion_devolucion(osv.osv_memory):
    _name = 'pos_distefano.anulacion_devolucion'
    _description = 'Anulacion/Devolucion'

    def onchange_pedido(self, cr, uid, ids, pedido, context=None):
        if not context:
            context = {}
        session = False

        if pedido:
            order = self.pool.get('pos.order').browse(cr, uid, pedido, context=context)
            lineas = []

            for l in order.lines:
                if not l.devuelto:
                    lineas.append({'linea': l.id, 'cantidad': l.qty})

            return {'value': {'lineas': lineas}}

        return {'value': {'lineas': []}}

    def procesar(self, cr, uid, ids, context=None):
        clone_list = []

        for d in self.browse(cr, uid, ids, context=context):
            current_session_ids = self.pool.get('pos.session').search(cr, uid, [
                ('state', '!=', 'closed'),
                ('user_id', '=', uid)], context=context)

            if not current_session_ids:
                raise osv.except_osv(_('Error!'), _('No tiene una sesion abierta'))

            if d.pedido.anulado:
                raise osv.except_osv(_('Error!'), _('Este pedido ya fue anulado.'))

            if d.pedido.pedido_original:
                raise osv.except_osv(_('Error!'), _('Este es una anulacion o devolucion, no puede ser anulado o devuelto nuevamente.'))

            if d.tipo == 'anular':

                for l in d.pedido.lines:
                    if l.devuelto:
                        raise osv.except_osv(_('Error!'), _('Este pedido ya fue devuelto y ya no puede ser anulado.'))

                if d.pedido.session_id.state != 'opened':
                    raise osv.except_osv(_('Error!'), _('La sesion del pedido ya fue cerrada y ya no se puede anular este pedido.'))

                result = self.pool.get('pos.order').refund(cr, uid, [d.pedido.id], context=context)
                clone_id = result['res_id']

                self.pool.get('pos.order').write(cr, uid, d.pedido.id, {'anulado': True}, context=context)
                self.pool.get('pos.order').write(cr, uid, clone_id, {'pedido_original': d.pedido.id, 'numero_factura': False}, context=context)
                d.pedido.invoice_id.action_cancel()

                for p in d.pedido.statement_ids:
                    self.pool.get('pos.order').add_payment(cr, uid, clone_id, {
                        'journal': p.journal_id.id,
                        'amount': -1 * p.amount,
                        'payment_name': p.name,
                    }, context=context)

                if self.pool.get('pos.order').test_paid(cr, uid, [clone_id]):
                    self.pool.get('pos.order').signal_workflow(cr, uid, [clone_id], 'paid')

                return

            else:

                clone_id = self.pool.get('pos.order').copy(cr, uid, d.pedido.id, {
                    'name': d.pedido.name + ' DEVOLUCION', # not used, name forced by create
                    'session_id': current_session_ids[0],
                    'date_order': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'pedido_original': d.pedido.id,
                    'numero_factura': False,
                    'lines': []
                }, context=context)
                clone_list.append(clone_id)

                for l in d.lineas:
                    line_clone_id = self.pool.get('pos.order.line').copy(cr, uid, l.linea.id, {
                        'order_id': clone_id,
                        'qty': -1 * l.cantidad,
                        'price_unit': l.linea.product_id.list_price
                    }, context=context)
                    self.pool.get('pos.order').write(cr, uid, d.pedido.id, {'devuelto': True}, context=context)

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
        'pedido': fields.many2one('pos.order', 'Pedido', required=True),
        'tipo': fields.selection([('anular', 'Anular'), ('devolver', 'Devolver')], 'Operacion', required=True),
        'lineas': fields.one2many('pos_distefano.anulacion_devolucion.linea', 'anulacion_devolucion', 'Lineas'),
    }

class pos_distefano_anulacion_devolucion_linea(osv.osv_memory):
    _name = 'pos_distefano.anulacion_devolucion.linea'
    _description = 'Devolucion linea'

    _columns = {
        'anulacion_devolucion': fields.many2one('pos_distefano.anulacion_devolucion', 'Anulacion/Devolucion', required=True, ondelete='cascade'),
        'linea': fields.many2one('pos.order.line', 'Linea del pedido', required=True),
        'cantidad': fields.float('Cantidad', digits_compute=dp.get_precision('Product UoS')),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
