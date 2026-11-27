# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    # Non-stored carrier for the note collected by the stage note wizard. It
    # never creates a column: ``write`` pops it before the actual write.
    stage_note = fields.Text(
        store=False,
        readonly=True,
        help="Internal note posted together with the stage change.",
    )
    # Stages of the team that ask for a note. The client reads it from the
    # ticket to decide whether the wizard must be opened.
    stage_note_stage_ids = fields.Many2many(
        "helpdesk.stage",
        related="team_id.stage_note_stage_ids",
        help="Stages of the team that ask for a note.",
    )

    def write(self, vals):
        note = vals.pop("stage_note", False)
        stage_id = vals.get("stage_id")
        res = super().write(vals)
        if note and stage_id:
            self.message_post(
                body=_(
                    "Stage changed to %(stage)s with note:\n%(note)s",
                    stage=self.env["helpdesk.stage"].browse(stage_id).name,
                    note=note,
                ),
                subtype_xmlid="mail.mt_note",
            )
        return res
