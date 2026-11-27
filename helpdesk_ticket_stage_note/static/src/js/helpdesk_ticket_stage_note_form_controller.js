/** @odoo-module **/

import {useService} from "@web/core/utils/hooks";
import {registry} from "@web/core/registry";
import {formView} from "@web/views/form/form_view";
import {FormController} from "@web/views/form/form_controller";

import {requireStageNote} from "./stage_note_dialog";

export class HelpdeskTicketStageNoteController extends FormController {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    }

    /**
     * Require a note when the stage is changed to a stage that asks for one.
     * Returning false aborts the save, leaving every other unsaved edit intact.
     *
     * @override
     */
    async onWillSaveRecord(record, changes) {
        const services = {dialog: this.dialogService, orm: this.orm};
        return requireStageNote(services, record, changes);
    }
}

registry.category("views").add("helpdesk_ticket_stage_note_form", {
    ...formView,
    Controller: HelpdeskTicketStageNoteController,
});
