# Changelog

## 17.0.1.1.0

- Add `stage_note_stage_ids` on `helpdesk.team`: the stages that ask for a note.
  Each team picks its own stages in the *Ask for a Note* setting.
- Only open the note wizard for those stages, in the form and in the kanban.
- Title the dialog "Reason for setting stage to <stage>".
- Prefix the chatter message: `Stage changed to <stage> with note:` followed by
  the note.
- Post the note only for a configured stage, whatever the client sends.
- Expose the team stages on the ticket as a non-stored `related` field, so the
  form and kanban read them from the record without an extra call.
- Add German translations.

## 17.0.1.0.0

- Add the `helpdesk_ticket_stage_note` module.
- Add a `helpdesk.ticket.stage.note.wizard` transient model that collects a
  chatter note for a stage change. The wizard never writes the ticket.
- Add a non-stored `stage_note` carrier on `helpdesk.ticket`; `write()` posts it
  as an internal note (`mail.mt_note`) in the same transaction as the stage change.
- Add a form `js_class` that opens the wizard from `onWillSaveRecord` and sends
  `stage_id` and `stage_note` in one `web_save`; cancelling aborts the save while
  keeping other unsaved edits.
- Add a kanban `js_class` that opens the wizard before `moveRecord`, so a
  cancelled drag leaves the card in its column.
- Document the limitation: writes made outside the UI change the stage without a
  note.
