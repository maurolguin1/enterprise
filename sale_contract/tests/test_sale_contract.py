# -*- coding: utf-8 -*-
from odoo.addons.sale_contract.tests.common_sale_contract import TestContractCommon
from odoo.tools import mute_logger


class TestContract(TestContractCommon):

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_template(self):
        """ Test behaviour of on_change_template """
        Contract = self.env['sale.subscription']

        # on_change_template on existing record (present in the db)
        self.contract.template_id = self.contract_tmpl
        self.contract.on_change_template()
        self.assertTrue(len(self.contract.recurring_invoice_line_ids.ids) == 0, 'sale_contract: recurring_invoice_line_ids copied on existing sale.subscription record')

        # on_change_template on cached record (NOT present in the db)
        temp = Contract.new({'name': 'CachedContract',
                             'type': 'contract',
                             'state': 'open',
                             'partner_id': self.user_portal.partner_id.id
                             })
        temp.update({'template_id': self.contract_tmpl.id})
        temp.on_change_template()
        self.assertTrue(temp.recurring_invoice_line_ids.name, 'sale_contract: recurring_invoice_line_ids not copied on new cached sale.subscription record')

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_sale_order(self):
        """ Test sale order line copying for recurring products on confirm"""
        self.sale_order.action_confirm()
        self.assertTrue(len(self.contract.recurring_invoice_line_ids.ids) == 1, 'sale_contract: recurring_invoice_line_ids not created when confirming sale_order with recurring_product')
        self.assertEqual(self.sale_order.state, 'done', 'sale_contract: so state should be after confirmation done when there is a subscription')
        self.assertEqual(self.sale_order.subscription_management, 'upsell', 'sale_contract: so should be set to "upsell" if not specified otherwise')

    def test_renewal(self):
        """ Test contract renewal """
        res = self.contract.prepare_renewal_order()
        renewal_so_id = res['res_id']
        renewal_so = self.env['sale.order'].browse(renewal_so_id)
        self.assertTrue(renewal_so.subscription_management == 'renew', 'sale_contract: renewal quotation generation is wrong')
        self.contract.write({'recurring_invoice_line_ids': [(0, 0, {'product_id': self.product.id, 'name': 'TestRecurringLine', 'price_unit': 50, 'uom_id': self.product.uom_id.id})]})
        renewal_so.write({'order_line': [(0, 0, {'product_id': self.product.id, 'name': 'TestRenewalLine', 'product_uom': self.product.uom_id.id})]})
        renewal_so.action_confirm()
        lines = [line.name for line in self.contract.recurring_invoice_line_ids]
        self.assertTrue('TestRecurringLine' not in lines, 'sale_contract: old line still present after renewal quotation confirmation')
        self.assertTrue('TestRenewalLine' in lines, 'sale_contract: new line not present after renewal quotation confirmation')
        self.assertEqual(renewal_so.state, 'done', 'sale_contract: so state should be after confirmation done when there is a subscription')
        self.assertEqual(renewal_so.subscription_management, 'renew', 'sale_contract: so should be set to "renew" in the renewal process')
