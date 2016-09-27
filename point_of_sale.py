import logging
import time
import math

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero

_logger = logging.getLogger(__name__)

class pos_order(osv.osv):
    _inherit = "pos.order"

    _columns= {
        'pedido_original' : fields.many2one('pos.order', 'Pedido original'),
        'numero_factura' : fields.char('Numero de factura a generar'),
        'anulado' : fields.boolean('Anulado'),
        'devuelto': fields.boolean('Devuelto'),
        'sale_manual_journal': fields.related('session_id', 'config_id', 'journal_manual_id', relation='account.journal', type='many2one', string='Diario de ventas manual', store=True, readonly=True),
    }

    def _order_fields(self, cr, uid, ui_order, context=None):
        return {
            'name':         ui_order['name'],
            'user_id':      ui_order['user_id'] or False,
            'session_id':   ui_order['pos_session_id'],
            'lines':        ui_order['lines'],
            'pos_reference':ui_order['name'],
            'partner_id':   ui_order['partner_id'] or False,
            'numero_factura': ui_order['numero_factura'] or False,
        }

    def mix_and_match(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids, context=context):
            if o.pedido_original:
                continue

            productos = []
            cantidad = 0

            for l in o.lines:
                if l.product_id.type != 'service':
                    precio = l.product_id.list_price
                    for i in range(int(l.qty)):
                        productos.append({'linea': l, 'precio': precio, 'precio_original': precio})
                    cantidad += int(l.qty)

            productos.sort(key=lambda l: l['precio'])

            restantes = int(math.floor(cantidad/2.0))
            incremento = int(math.ceil(cantidad/2.0))

            for i in range(restantes):
                descuento = productos[i]['precio']
                total = productos[i]['precio'] + productos[i+incremento]['precio'];
                productos[i]['precio'] = productos[i]['precio'] - ( productos[i]['precio'] / total * descuento );
                productos[i+incremento]['precio'] = productos[i+incremento]['precio'] - ( productos[i+incremento]['precio'] / total * descuento );

            for p in productos:

                # Si este producto no cambio de precio es por que es
                # uno impar, por lo que tiene un 25% de descuento
                precio = p['precio']
                if p['precio'] == p['precio_original']:
                    precio = p['precio'] * 0.75

                n_id = self.pool.get('pos.order.line').copy(cr, uid, p['linea'].id, {'qty': 1, 'price_unit': precio}, context=context)
                _logger.warn(n_id)

            p_ids = set()
            for p in productos:
                p_ids.add(p['linea'].id)
            self.pool.get('pos.order.line').unlink(cr, uid, p_ids, context=context)

            # Si es una devolucion
            if o.pedido_original:
                if len(o.lines) == 2:
                    pareja = o.lines.sorted(key=lambda l: l.price_subtotal_incl)
                    if pareja[0].price_subtotal_incl < 0 and pareja[0].product_id.list_price == pareja[1].product_id.list_price:
                        self.pool.get('pos.order.line').write(cr, uid, pareja[0].id, {'price_unit': pareja[0].product_id.list_price})
                        self.pool.get('pos.order.line').write(cr, uid, pareja[1].id, {'price_unit': pareja[1].product_id.list_price})
        return True

    def action_invoice(self, cr, uid, ids, context=None):
        action = super(pos_order, self).action_invoice(cr, uid, ids, context=context)
        for o in self.browse(cr, uid, ids, context=context):
            if not o.numero_factura and o.sale_manual_journal:
                self.pool.get('account.invoice').write(cr, uid, action['res_id'], {'journal_id': o.sale_manual_journal.id}, context=context)
        return action

    def action_paid(self, cr, uid, ids, context=None):
        result = super(pos_order, self).action_paid(cr, uid, ids, context=context)
        for o in self.browse(cr, uid, ids, context=context):
            if o.amount_total > 0:
                if not o.partner_id:
                    self.write(cr, uid, [o.id], {'partner_id': 320334}, context=context)
                self.action_invoice(cr, uid, [o.id], context)
                self.pool['account.invoice'].signal_workflow(cr, uid, [o.invoice_id.id], 'invoice_open')
        return result

    def _process_order(self, cr, uid, order, context=None):
        session = self.pool.get('pos.session').browse(cr, uid, order['pos_session_id'], context=context)

        if session.state == 'closing_control' or session.state == 'closed':
            session_id = self._get_valid_session(cr, uid, order, context=context)
            session = self.pool.get('pos.session').browse(cr, uid, session_id, context=context)
            order['pos_session_id'] = session_id

        order_id = self.create(cr, uid, self._order_fields(cr, uid, order, context=context),context)
        journal_ids = set()
        for payments in order['statement_ids']:
            self.add_payment(cr, uid, order_id, self._payment_fields(cr, uid, payments[2], context=context), context=context)
            journal_ids.add(payments[2]['journal_id'])

        if session.sequence_number <= order['sequence_number']:
            session.write({'sequence_number': order['sequence_number'] + 1})
            session.refresh()

        if not float_is_zero(order['amount_return'], self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')):
            # cash_journal = session.cash_journal_id.id
            cash_journal = False
            if session.config_id.journal_negativo_id:
                cash_journal =  session.config_id.journal_negativo_id.id
            if not cash_journal:
                # Select for change one of the cash journals used in this payment
                cash_journal_ids = self.pool['account.journal'].search(cr, uid, [
                    ('type', '=', 'cash'),
                    ('id', 'in', list(journal_ids)),
                ], limit=1, context=context)
                if not cash_journal_ids:
                    # If none, select for change one of the cash journals of the POS
                    # This is used for example when a customer pays by credit card
                    # an amount higher than total amount of the order and gets cash back
                    cash_journal_ids = [statement.journal_id.id for statement in session.statement_ids
                                        if statement.journal_id.type == 'cash']
                    if not cash_journal_ids:
                        raise osv.except_osv( _('error!'),
                            _("No cash statement found for this session. Unable to record returned cash."))
                cash_journal = cash_journal_ids[0]
            self.add_payment(cr, uid, order_id, {
                'amount': -order['amount_return'],
                'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'payment_name': _('return'),
                'journal': cash_journal,
            }, context=context)
        return order_id

class pos_order_line(osv.osv):
    _inherit = "pos.order.line"

    def _get_precio_unitario(self, cr, uid, ids, fieldnames, args, context=None):
        result = dict.fromkeys(ids, False)
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = line.price_unit
        return result

    _columns= {
         'devuelto' : fields.boolean('Devuelto'),
         'precio_unitario': fields.function(_get_precio_unitario, type="float", string="Precio Unit.", digits_compute=dp.get_precision('Account')),
    }

class pos_confirm(osv.osv_memory):
    _inherit = 'pos.confirm'

    def action_confirm(self, cr, uid, ids, context=None):
        order_obj = self.pool.get('pos.order')
        ids = order_obj.search(cr, uid, [('state','=','paid')], context=context)
        for order in order_obj.browse(cr, uid, ids, context=context):
            todo = True
            for line in order.statement_ids:
                if line.statement_id.state != 'confirm':
                    todo = False
                    break
            if todo:
                order.signal_workflow('done')

        # Check if there is orders to reconcile their invoices
        ids = order_obj.search(cr, uid, [('state','=','invoiced'),('invoice_id.state','=','open')], context=context)
        for order in order_obj.browse(cr, uid, ids, context=context):
            invoice = order.invoice_id
            data_lines = [x.id for x in invoice.move_id.line_id if x.account_id.id == invoice.account_id.id]
            for st in order.statement_ids:
                data_lines += [x.id for x in st.journal_entry_id.line_id if x.account_id.id == invoice.account_id.id]
            self.pool.get('account.move.line').reconcile(cr, uid, data_lines, context=context)
        return {}

class pos_config(osv.osv):
    _inherit = "pos.config"

    def _pedidos_pendientes(self, cr, uid, ids, fieldnames, args, context=None):
        result = dict.fromkeys(ids, False)
        for c in self.browse(cr, uid, ids, context=context):
            total = 0
            sesiones = self.pool.get('pos.session').search(cr, uid, [('config_id','=',c.id),('state','=','opened')], context=context)
            for s in self.pool.get('pos.session').browse(cr, uid, sesiones, context=context):
                for o in s.order_ids:
                    if o.state == 'paid' and o.numero_factura:
                        total += 1
            result[c.id] = total
        return result

    _columns= {
        'numero_siguiente' : fields.related('journal_id', 'sequence_id', 'number_next', type="integer", string="Numero siguiente"),
        'prefijo' : fields.related('journal_id', 'sequence_id', 'prefix', type="char", string="Prefijo"),
        'relleno' : fields.related('journal_id', 'sequence_id', 'padding', type="integer", string="Relleno"),
        'pedidos_pendientes' : fields.function(_pedidos_pendientes, type="integer", string="Pedidos de pendientes"),
        'journal_manual_id' : fields.many2one('account.journal', 'Diario de ventas manual', domain=[('type', '=', 'sale')]),
        'journal_negativo_id' : fields.many2one('account.journal', 'Diario de pagos negativos'),
        'devoluciones' : fields.boolean('Se pueden hacer devoluciones'),
    }

class pos_details(osv.osv_memory):
    _inherit = 'pos.details'

    _columns = {
        'date_start': fields.datetime('Date Start', required=True),
        'date_end': fields.datetime('Date End', required=True),
    }

class pos_session(osv.osv):
    _inherit = 'pos.session'

    def _confirm_orders(self, cr, uid, ids, context=None):
        for session in self.browse(cr, uid, ids, context=context):
            for order in session.order_ids:
                if order.amount_total > 0:
                    if not order.invoice_id:
                        raise osv.except_osv(
                            _('Error!'),
                            _("No se puede cerrar la sesion por que existen pedidos que no tienen facturas creadas."))
                    if order.invoice_id and order.invoice_id.state not in ('open', 'cancel'):
                        raise osv.except_osv(
                            _('Error!'),
                            _("No se puede cerrar la sesion por que existen pedidos que tienen facturas que no han sido validadas."))

        return super(pos_session, self)._confirm_orders(cr, uid, ids, context=context)
