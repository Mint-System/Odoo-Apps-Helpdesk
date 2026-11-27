# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    change_category = fields.Selection(
        selection=[
            ("software", "Software-Installation, Update oder Upgrade"),
            ("hardware", "Hardware Austausch oder Anpassung"),
            ("configuration", "Konfiguration Anpassung bestehender Einstellungen"),
            ("policy", "Policy: Anpassung von Richtlinien"),
            ("security", "Security: Sicherheitsmassnahmen"),
            ("migration", "Migration: System- oder Datenmigration"),
            ("project", "Projekt: Projektbedingte Änderung"),
            ("extension", "Erweiterung: Ausbau bestehender Infrastruktur"),
            ("optimization", "Optimierung: Verbesserung bestehender Systeme"),
            ("decommission", "Rückbau: Abbau oder Ausserbetriebnahme"),
            ("other", "Sonstiges: Nicht eindeutig zuordenbare Änderung"),
        ],
        string="Category",
        help="Firmware, Software, Hardware, Konfiguration, Policy, Security, "
        "Migration, Projekt, Erweiterung, Optimierung, Rückbau, Sonstiges",
    )
    change_reason = fields.Text(
        string="Reason",
        help="Beschreib kurz die Notwendigkeit",
    )
    risk = fields.Selection(
        selection=[
            ("low", "Niedrig"),
            ("medium", "Mittel"),
            ("high", "Hoch"),
        ],
        string="Risk",
        help="Niedrig = Probleme unwahrscheinlich, Mittel = Probleme möglich, "
        "Hoch = Probleme sehr wahrscheinlich",
    )
    impact = fields.Selection(
        selection=[
            ("low", "Niedrig"),
            ("medium", "Mittel"),
            ("high", "Hoch"),
        ],
        string="Impact",
        help="Niedrig = Keine Betriebseinschränkung, Mittel = Geringe "
        "Betriebseinschränkung, Hoch = Erhebliche Betriebseinschränkung",
    )
    implementation_plan = fields.Text(
        string="Implementation Plan",
        help="Beschreib kurz deine Planung",
    )
    rollback_plan = fields.Text(
        string="Rollback Plan",
        help="Beschreib kurz, wie du die Änderung rückgängig machst",
    )
    test_plan = fields.Text(
        string="Test Plan",
        help="Beschreib kurz die geplanten Prüfungen",
    )
    planned_execution = fields.Datetime(
        string="Planned Execution",
        help="Gib den geplanten Zeitpunkt der Umsetzung an",
    )
