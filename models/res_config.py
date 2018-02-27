from odoo import fields, models, api

class DtsConfig(models.Model):
    _name = 'dts.config'

    show_document_type = fields.Boolean(string="Show Document Type", default=True)
    document_type_id_default = fields.Many2one(comodel_name="dts.document.type", string="Document Type", required=True,
                                               domain="[('active', '=', True)]")
    show_delivery_method = fields.Boolean(string="Show Delivery Method", default=True)
    delivery_method_id_default = fields.Many2one(comodel_name="dts.document.delivery", string="Delivery Method",
                                                 domain="[('active', '=', True)]")
class DtsConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'dts.config.settings'

    show_document_type = fields.Boolean(string="Show Document Type", default=True)
    document_type_id_default = fields.Many2one(comodel_name="dts.document.type", string="Document Type", required=True, domain="[('active', '=', True)]")
    show_delivery_method = fields.Boolean(string="Show Delivery Method", default=True)
    delivery_method_id_default = fields.Many2one(comodel_name="dts.document.delivery",string="Delivery Method", domain="[('active', '=', True)]")

    @api.model
    def default_get(self, fields):
        vals = {}
        res = super(DtsConfiguration, self).default_get(fields)
        if res:
            rec = self.env['dts.config'].browse(1)
            if rec:
                vals['show_document_type'] = rec.show_document_type
                vals['document_type_id_default'] = rec.document_type_id_default.id
                vals['show_delivery_method'] = rec.show_delivery_method
                vals['delivery_method_id_default'] = rec.delivery_method_id_default.id
                res.update(vals)
        return res

    @api.multi
    def set_config_settings(self):
        vals = {}

        vals['show_document_type'] = self.show_document_type
        vals['document_type_id_default'] = self.document_type_id_default.id
        vals['show_delivery_method'] = self.show_delivery_method
        vals['delivery_method_id_default'] = self.delivery_method_id_default.id

        rec = self.env['dts.config'].search([('id','=',1)])
        if not rec:
            rec.create(vals)
        else:
            rec.write(vals)

        # menu_rec = self.env['ir.ui.menu']
        #
        # active = False
        # menu_type_id = self.env.ref('dts.menu_dts_document_type').id
        # res = menu_rec.search([('id','=',menu_type_id)])
        # if self.show_document_type:
        #     active = True
        # res.write({'active':active})
        #
        # menu_delivery_id = self.env.ref('dts.menu_dts_document_delivery').id
        # active = False
        # res = menu_rec.search([('id','=',menu_delivery_id)])
        # if self.show_delivery_method:
        #     active = True
        # res.write({'active':active})

        return rec