# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    stage_note_stage_ids = fields.Many2many(
        "helpdesk.stage",
        relation="helpdesk_team_stage_note_stage_rel",
        string="Ask for a Note",
        domain="[('id', 'in', stage_ids)]",
        help="Changing a ticket to one of these stages asks for a note that " "is posted to the chatter.",
    )
