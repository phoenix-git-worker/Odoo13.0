import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class DalethPartherType(models.Model):
    _inherit = 'daleth.partner.type'
    _description = 'Extend model with Sovtes type'

    is_sovtes = fields.Boolean(
        default=False,
    )
