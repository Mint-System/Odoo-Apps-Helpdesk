# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Helpdesk Ticket Stage Note",
    "summary": """
        Prompt for a chatter text at specific stage changes.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Repository",
    "development_status": "Production/Stable",
    "version": "17.0.1.1.0",
    "license": "AGPL-3",
    "depends": ["helpdesk"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/helpdesk_ticket_stage_note_wizard_views.xml",
        "views/helpdesk_team_views.xml",
        "views/helpdesk_ticket_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "helpdesk_ticket_stage_note/static/src/js/*.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
