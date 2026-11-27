# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskTicketStageNoteWizard(models.TransientModel):
    _name = "helpdesk.ticket.stage.note.wizard"
    _description = "Helpdesk Ticket Stage Note Wizard"

    ticket_id = fields.Many2one(
        "helpdesk.ticket",
        string="Ticket",
        required=True,
        ondelete="cascade",
    )
    stage_id = fields.Many2one(
        "helpdesk.stage",
        string="New Stage",
        readonly=True,
        help="Stage the ticket is moved to.",
    )
    note = fields.Text(
        required=True,
        help="Note posted to the ticket chatter.",
    )
