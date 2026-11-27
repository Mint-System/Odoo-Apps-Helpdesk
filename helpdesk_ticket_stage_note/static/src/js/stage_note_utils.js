/** @odoo-module **/

/**
 * Ids of the team stages that ask for a note, carried on the ticket record.
 *
 * @param {Object} record an `helpdesk.ticket` record (form or kanban)
 * @returns {Number[]}
 */
export function stageNoteStageIds(record) {
    const stages = record.data.stage_note_stage_ids;
    return stages ? [...stages.currentIds] : [];
}

/**
 * @param {Object} record an `helpdesk.ticket` record (form or kanban)
 * @param {Number|Boolean} stageId the stage the ticket is set to
 * @returns {Boolean} whether the note wizard must be opened
 */
export function isStageNoteStage(record, stageId) {
    return Boolean(stageId) && stageNoteStageIds(record).includes(stageId);
}
