/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";

import {isStageNoteStage} from "./stage_note_utils";

export const STAGE_NOTE_WIZARD_MODEL = "helpdesk.ticket.stage.note.wizard";

/**
 * Read the display name of a stage.
 *
 * @param {Object} orm the orm service
 * @param {Number} stageId
 * @returns {Promise<String>} the stage name, empty when it cannot be read
 */
async function readStageName(orm, stageId) {
    const [stage] = await orm.read("helpdesk.stage", [stageId], ["display_name"]);
    return stage ? stage.display_name : "";
}

/**
 * Ask the user for a note to post together with a ticket stage change.
 *
 * The wizard is passive: it never writes the ticket, the caller writes the
 * stage and the note in a single call.
 *
 * @param {Object} dialog the dialog service
 * @param {Object} orm the orm service, used to read the target stage name
 * @param {Number} ticketId
 * @param {Number} stageId target stage
 * @returns {Promise<String|null>} the note, or null when the user cancelled
 */
async function askStageNote(dialog, orm, ticketId, stageId) {
    const name = await readStageName(orm, stageId);
    return new Promise((resolve) => {
        dialog.add(
            FormViewDialog,
            {
                resModel: STAGE_NOTE_WIZARD_MODEL,
                context: {
                    default_ticket_id: ticketId,
                    default_stage_id: stageId,
                },
                title: _t("Reason for setting stage to %s", name),
                onRecordSaved: (record) => resolve(record.data.note || null),
                onRecordDiscarded: () => resolve(null),
            },
            {onClose: () => resolve(null)}
        );
    });
}

/**
 * Require a note when a ticket is saved with a stage that asks for one.
 *
 * The note is added to `changes`, the payload about to be sent to `web_save`,
 * so the stage and the note are written in one call. Returning false aborts the
 * save. New tickets are skipped: their stage comes from the team default.
 *
 * @param {Object} services the `dialog` and `orm` services
 * @param {Object} record the `helpdesk.ticket` record being saved
 * @param {Object} changes the values about to be written
 * @returns {Promise<Boolean|undefined>} false to abort the save
 */
export async function requireStageNote({dialog, orm}, record, changes) {
    if (
        !record.resId ||
        !("stage_id" in changes) ||
        !isStageNoteStage(record, changes.stage_id)
    ) {
        return;
    }
    const note = await askStageNote(dialog, orm, record.resId, changes.stage_id);
    if (note === null) {
        return false;
    }
    changes.stage_note = note;
}
