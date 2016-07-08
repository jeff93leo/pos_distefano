# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
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

from openerp.osv import osv
from openerp.tools.translate import _
from datetime import datetime, timedelta

class ReportCierre(osv.AbstractModel):
    _name = 'report.pos_distefano.report_cierre'

    def subtotal_ventas(self, s):
        total = 0
        for o in s.order_ids:
            total += o.amount_total
        return total

    def subtotal_ingresos(self, s):
        total = 0
        for st in s.statement_ids:
            total += st.total_entry_encoding
        return total

    def lineas_ventas(self, docs):
        lineas = []
        for s in docs:
            for o in s.order_ids:
                lineas.append(o)
        return lineas

    def total_ventas(self, docs):
        total = 0
        for s in docs:
            for o in s.order_ids:
                total += o.amount_total
        return total

    def lineas_ingresos(self, docs):
        diarios = {}
        for s in docs:
            for st in s.statement_ids:
                if st.journal_id.id not in diarios:
                    diarios[st.journal_id.id] = {'diario': st.journal_id, 'balance_inicial': 0, 'total_ventas': 0, 'balance_final': 0, 'diferencia': 0}
                diarios[st.journal_id.id]['balance_inicial'] += st.balance_start
                diarios[st.journal_id.id]['total_ventas'] += st.total_entry_encoding
                diarios[st.journal_id.id]['balance_final'] += st.balance_end_real
                diarios[st.journal_id.id]['diferencia'] += st.difference
        return diarios.values()

    def total_ingresos(self, docs):
        total = 0
        for s in docs:
            for st in s.statement_ids:
                total += st.total_entry_encoding
        return total

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        session_obj = self.pool['pos.session']

        report = report_obj._get_report_from_name(cr, uid, 'pos_distefano.report_cierre')
        sessions = session_obj.browse(cr, uid, ids, context=context)

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': sessions,
            'subtotal_ventas': self.subtotal_ventas,
            'subtotal_ingresos': self.subtotal_ingresos,
            'lineas_ventas': self.lineas_ventas,
            'total_ventas': self.total_ventas,
            'lineas_ingresos': self.lineas_ingresos,
            'total_ingresos': self.total_ingresos,
        }

        return report_obj.render(cr, uid, ids, 'pos_distefano.report_cierre', docargs, context=context)
