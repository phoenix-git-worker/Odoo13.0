import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _description = 'Product Product'

    kw_sovtes_checkbox = fields.Boolean(
        string='Sovtes',
        default=False
    )
