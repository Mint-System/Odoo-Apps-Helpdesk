---
commit_ref: 61b0796664d76412d5a3cf99d5fac0198d10a5bd
title: "helpdesk ticket stage note check code quality"
author: "laurens kooijman <laurenskooijman@gmail.com>"
session_id: 01a21c0d-1bd3-7581-99d0-3ba039c9b552
action: execute
state: completed
date_completed: 2026-11-27
harness: pi
provider: mistral
model: deepseek-v4-1-flash-1017
input_tokens: 318753
output_tokens: 37818
---

# helpdesk ticket stage note check code quality

Note: @Clanker refers to the "ai agent" (you) who is working on this prompt file.

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` to get an understanding of the project
- Read task section and prepare a list of todos
- Update the todo list while working on task

@Clanker When task is completed set frontmatter state to review. If you have access to session info add token count and session id. Prompt the author to verify the results.

## Task

I want you to take the role of code reviewer. Take a critical look at the module in `addons/helpdesk/helpdesk_ticket_stage_note`. 

I want you to review the code in general, identify
- superfluous code (I prefer the code to be concise and clear instead of checking everything and become bloated)
- code that is unclear for a later developer
- what you would change.

Questions I have:
- in the write function in helpdesk_ticket.py. Is this additional check really necessary?
         post_note = note and any(stage_id and stage_id in ticket.team_id.stage_note_stage_ids.ids for ticket in self)

Don't change anything. Please report on the changes that you would make.

## Worklog

Reviewed `addons/helpdesk/helpdesk_ticket_stage_note` and applied the changes
the author approved. Seven findings were fixed; four were deliberately left open.

### Kanban: `moveRecord` override replaced by a save hook

The 45-line `RelationalModel.DynamicGroupList.moveRecord` override (group
lookups plus a `record.update` monkey-patch guarded by `try/finally`) is gone.
The kanban now registers `onWillSaveRecord` through `get modelParams()`, the same
hook the form already used, so both views share one rule and one code path.
`helpdesk_ticket_stage_note_kanban_model.js` and `..._kanban_view.js` are deleted;
`helpdesk_ticket_stage_note_kanban_controller.js` replaces them.

### Dialog: custom button template dropped

`static/src/xml/stage_note_dialog.xml` re-declared the Discard button that
`web.FormViewDialog.ToOne.buttons` already inherits from `web.FormView.Buttons`,
including a hardcoded `data-hotkey="j"`. The file, the `buttonTemplate` option,
the `static/src/xml/*.xml` asset entry and the now-orphaned `Cancel` entry in
`de.po` were removed. The dialog renders core's Save & Close (`c`/Enter) and
Discard (`j`) buttons; the cancel label reads "Discard" instead of "Cancel".

### Server: `_compute_stage_note` removed

The non-stored `stage_note` carrier is now `fields.Text(store=False, readonly=True)`.
`fields.py:1250` caches `False` for a non-stored, non-computed field, which is
exactly what the compute loop returned. Both views keep `force_save="1"`, so the
client still sends the value in `changes`.

### Shared guard, single resolve

`stageNoteStageIds` lost its untested `Array.isArray` branch, and `stageName()`
was deleted — it returned `""` for the kanban case, so `askStageNote` always fell
back to `readStageName` anyway. The guard now lives once in `requireStageNote`;
both controllers are three-line delegates that differ only in which dialog
service they pass. The form no longer calls `super.onWillSaveRecord` (the base
controller never defines it), and `askStageNote` resolves from one place: closing
the dialog resolves `null`, so the save can never hang.

### Files

- `static/src/js/helpdesk_ticket_stage_note_kanban_controller.js` (new)
- `static/src/js/helpdesk_ticket_stage_note_kanban_model.js` (deleted)
- `static/src/js/helpdesk_ticket_stage_note_kanban_view.js` (deleted)
- `static/src/xml/stage_note_dialog.xml` (deleted)
- `static/src/js/stage_note_dialog.js`, `stage_note_utils.js`,
  `helpdesk_ticket_stage_note_form_controller.js`, `models/helpdesk_ticket.py`,
  `__manifest__.py`, `i18n/de.po` (edited)

The `orm` service stays on both controllers: `useService` throws outside a
component's render cycle (`owl.js:2387`), so the stage-name read cannot be
hoisted into the dialog module.

### Verification

`./task lint` exits 0 with no findings for the module; `node --check` passes on
all four JS files; `msgfmt --check-format` passes on `de.po`. UI behaviour was
not exercised — verifying a drag between stages and the dialog's Enter/`j` keys
is left to the author.

### Left open by choice

`readme/USAGE.md` is empty; `write()` has no docstring for the dropped-note case;
the `//form` xpath in `helpdesk_ticket_views.xml` is broader than needed; the
`%s` vs `%(...)s` placeholder styles differ between JS and Python.

The `write()` configuration check was removed by the author: a note is now
posted whenever `stage_id` is written, with `isStageNoteStage()` in the client as
the only filter. Tests are the author's to add.

@Clanker If author confirms results set frontmatter state to completed, otherwise to aborted. Update date, harness, provider and model. If you have access to session info update token count. Finally, update the changelog with the most important changes.
