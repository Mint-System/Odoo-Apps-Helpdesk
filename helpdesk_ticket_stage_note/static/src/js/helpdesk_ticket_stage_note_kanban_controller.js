/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {KanbanController} from "@web/views/kanban/kanban_controller";

import {requireStageNote} from "./stage_note_dialog";

export class HelpdeskTicketStageNoteKanbanController extends KanbanController {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    }

    /**
     * The kanban base controller only registers `onRecordSaved`; add the
     * `onWillSaveRecord` hook the model asks for before saving a record.
     *
     * @override
     */
    get modelParams() {
        const params = super.modelParams;
        return {
            ...params,
            hooks: {
                ...params.hooks,
                onWillSaveRecord: this.onWillSaveRecord.bind(this),
            },
        };
    }

    /**
     * Require a note when a card is dragged to another stage. Returning false
     * aborts the save, leaving the card in its column.
     *
     * @override
     */
    async onWillSaveRecord(record, changes) {
        const services = {dialog: this.dialog, orm: this.orm};
        return requireStageNote(services, record, changes);
    }
}

registry.category("views").add("helpdesk_ticket_stage_note_kanban", {
    ...kanbanView,
    Controller: HelpdeskTicketStageNoteKanbanController,
});
