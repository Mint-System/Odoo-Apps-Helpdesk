---
commit_ref: 24e7c682e0681bb23ee2464739b8e79dd967bbca
title: "new module helpdesk ticket stage note"
author: "laurens kooijman <laurenskooijman@gmail.com>"
session_id: 01a21808-d6b0-7041-8b98-8b5710173581
action: execute
state: completed
date_completed: 2026-11-26
harness: pi
provider: mistral
model: deepseek-v4-1-flash-1017
input_tokens: 544228
output_tokens: 53682
---

# new module helpdesk ticket stage note

Note: @Clanker refers to the "ai agent" (you) who is working on this prompt file.

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` to get an understanding of the project
- Read task section and prepare a list of todos
- Update the todo list while working on task

@Clanker When task is completed set frontmatter state to review. If you have access to session info add token count and session id. Prompt the author to verify the results.

## Task

## Specification

**Module:** `helpdesk_ticket_stage_note` (in `addons/helpdesk/`)

**Purpose:** When a `helpdesk.ticket` changes stage, require the user to enter a note
that is posted to the ticket chatter, before the stage is written. The interaction is
cancellable: no stage change means no note, no note means no stage change.

### Behaviour

| Actor | Expected |
|---|---|
| Change stage in form statusbar | Wizard opens before write. Confirm → stage + note committed. Cancel → nothing changes. |
| Drag card to another stage column | Same wizard, same guarantees. Cancel → card snaps back. |
| Confirm / cancel | Both reachable; `Esc` and the X count as cancel. |
| Non-UI write (import, RPC, mass edit) | No wizard (impossible by design); stage change proceeds without a note. |
| Stage is unchanged by the save | No wizard. |

### Data model

`helpdesk.ticket.stage.note.wizard` (`TransientModel`):

| Field | Type | Notes |
|---|---|---|
| `ticket_id` | Many2one `helpdesk.ticket`, required, ondelete cascade | |
| `stage_id` | Many2one `helpdesk.stage`, read-only display | Target stage, shown for context |
| `note` | Text, required | Chatter message body |

The wizard is **passive**: it collects the note and returns it to the caller. It must
**not** write the ticket — the form (or the kanban `moveRecord`) performs the write.

`helpdesk.ticket` gains `stage_note = fields.Text(store=False, compute=lambda self: None)`
— a non-stored carrier that never creates a column. Its `write()` pops the value, calls
`super().write(vals)`, then posts it:

```python
def write(self, vals):
    note = vals.pop("stage_note", False)
    res = super().write(vals)
    if note:
        self.message_post(body=note, subtype_xmlid="mail.mt_note")
    return res
```

One RPC, one transaction: no stage change without a note, no note without a stage change.

### Client

**Form.** New `js_class` subclassing the helpdesk form view. `onWillSaveRecord(record,
changes)`:

1. `"stage_id" not in changes` → `return true`, no wizard.
2. Open the wizard and await it. Cancel/close → `return false`; `record._save()` returns
   before the RPC, so nothing is written (the statusbar value is only a pending
   `_changes` entry, so it resets on the next render).
3. Confirm → `record.update({ stage_note: note })` and `return true`; the user's own save
   persists stage + note in one `web_save`.

Do **not** have the wizard write and then revert on cancel: 17.0 has no per-field revert,
and `record.discard()` clears `_changes` entirely (`record.js:523-544`), destroying every
other unsaved edit in the form.

**Kanban.** Subclass the existing `helpdesk_ticket_kanban` view with a
`RelationalModel.DynamicGroupList` subclass overriding `moveRecord`. If source and target
group differ and the view is grouped by `stage_id`, open the wizard **before**
`super.moveRecord(...)`. Cancel → `return` early; nothing is mutated yet, and 17.0
reverts if `record.update()` returns falsy (`dynamic_group_list.js:118-131`). Confirm →
`record.update({ stage_id, stage_note: note }, { save: true })` so the same Python hook
posts the note. Follow `odoo/addons/crm/static/src/views/crm_kanban/crm_kanban_model.js`
for the class/`Model` wiring.

Do not use `onRecordSaved` as the trigger or as the place to post the note: it runs after
the commit, so a dismissed dialog or a failed RPC leaves a stage change with no note.
Do not use an `@api.constrains` as the primary mechanism: it can only block with an error
dialog, not collect text.

### Out of scope
- Blocking non-UI writes; they proceed silently (documented limitation).
- Stage-specific required fields (that is `helpdesk_mgmt_stage_validation`'s job).
- Portal / website ticket views.

### Acceptance
1. Form: changing stage opens the wizard; cancel leaves stage and chatter unmodified, and
   any other unsaved field edits in the form are **retained**.
2. Form: confirm changes stage and adds exactly one `mail.mt_note` message in the same
   save (one `web_save` carrying both `stage_id` and `stage_note`).
3. Kanban: drag to another column opens the wizard; cancel keeps the card in its column.
4. Kanban: confirm moves the card and posts the note.
5. Saving an unrelated field posts no message and opens no wizard.
6. `stage_note` is never stored on `helpdesk.ticket`.

### References
- Dialog + save-cancel: `odoo/addons/hr/static/src/views/profile_form_view.js`,
  `enterprise/knowledge/static/src/js/knowledge_controller.js:173`
- Kanban drag hook: `odoo/addons/crm/static/src/views/crm_kanban/crm_kanban_model.js`
- Same-app `onWillSaveRecord`: `enterprise/helpdesk/static/src/views/helpdesk_team_form/helpdesk_team_form_controller.js:26`
- `wizard -> message_post`: `oca/helpdesk/helpdesk_mgmt_merge/wizard/helpdesk_ticket_merge.py:147`
- `stage_id` has `tracking=1`, so the stage change is already logged; the wizard note is
  the human reason, posted as an internal note right after it.
## Worklog

### Summary

The module is built and does what the prompt asks: every stage change of a
`helpdesk.ticket` is held back by a small passive wizard that demands a note, which
is then posted as an internal chatter message in the same transaction as the stage
change. Cancelling the wizard aborts the stage change and leaves everything else on
the form untouched. Server-side writes (imports, automations, the API) skip the
wizard and post nothing.

Two things are still open, and neither is a coding problem:

1. **It has not been tried in a real browser.** The browser automation cannot start
   in this environment, so I only verified the server side and the exact payload the
   client sends. Please walk the six acceptance criteria by hand.
2. **The module is currently uninstalled from the `17.0` database.** Installing it
   exposed a setup problem: `addons/helpdesk` is not a git submodule, so it is not on
   the addons path your server uses. Your server then has the module's data but not
   its code, and every helpdesk kanban view crashes with
   `ValueError: can only parse strings`. Uninstalling restored the kanban. To use the
   module, restart your server with `addons/helpdesk` in the addons path, then install
   it with `ODOO_ADDONS_PATH=addons/helpdesk ./task init-module 17.0 addons/helpdesk/helpdesk_ticket_stage_note`.

On tests: I had written eight unit tests, you asked me to delete them, they are gone.
The sibling `helpdesk_ticket_pureict` has none either.

The rest of this section is a technical handover, written so an agent or a later you
can pick the work up without rediscovering the traps.

### Status: code complete, module currently UNINSTALLED, needs a UI pass

Read the rest before changing anything. The implementation is finished; the open
items are environmental and manual.

### Where the code lives

`addons/helpdesk/helpdesk_ticket_stage_note/` (module built from the `create-module`
scaffold; `tests/` holds only the empty `TEST_INSTRUCTIONS.rst`, matching the sibling
`helpdesk_ticket_pureict`, which has no tests).

Files:

```
__manifest__.py                     # depends helpdesk; data: security, wizard views, ticket views
models/helpdesk_ticket.py           # stage_note carrier + write() hook
wizard/helpdesk_ticket_stage_note_wizard.py
wizard/helpdesk_ticket_stage_note_wizard_views.xml
views/helpdesk_ticket_views.xml     # form + kanban inherits (js_class, stage_note field)
security/ir.model.access.csv        # wizard: helpdesk.group_helpdesk_user + _manager
static/src/js/stage_note_dialog.js
static/src/js/helpdesk_ticket_stage_note_form_controller.js
static/src/js/helpdesk_ticket_stage_note_kanban_model.js
static/src/js/helpdesk_ticket_stage_note_kanban_view.js
static/src/xml/stage_note_dialog.xml
readme/USAGE.md                     # documents the non-UI limitation
CHANGELOG.md
```

### Server design

- `helpdesk.ticket.stage.note.wizard` (`TransientModel`): `ticket_id` (required,
  ondelete cascade), `stage_id` (read-only, context only), `note` (required). Passive:
  it never writes the ticket; the caller does.
- `helpdesk.ticket.stage_note`: non-stored `Text`, `compute="_compute_stage_note"` which
  assigns `False` per record. The compute must assign: `compute=lambda self: None`
  raises `ValueError: Compute method failed to assign ...` as soon as `web_read` runs.
- `helpdesk.ticket.write()`: pops `stage_note`, calls `super().write(vals)`, then
  `message_post(body=note, subtype_xmlid="mail.mt_note")` if truthy. One RPC, one
  transaction.

### Client design, and two non-obvious traps

1. `askStageNote(dialog, ticketId, stageId)` in `stage_note_dialog.js` opens the wizard
   via `FormViewDialog` + a custom `buttonTemplate`
   (`helpdesk_ticket_stage_note.StageNoteDialog.buttons`, inherits
   `web.FormViewDialog.ToOne.buttons`, adds an explicit *Cancel* that calls
   `discard`). Resolves the note on confirm, `null` on cancel / `Esc` / X.
2. **Form**: `onWillSaveRecord(record, changes)` receives `changes` = the snapshot
   `_getChanges()` took at `record.js:997`, *before* the hook. Mutating the record
   (`record.update({stage_note})`) does NOT reach that `web_save`. So the controller
   assigns `changes.stage_note = note` directly, and the view field carries
   `force_save="1"` so `_getChanges` cannot filter it out. Cancel returns `false`,
   which aborts before the RPC and never touches `_changes`, so other unsaved form
   edits survive (do not use `record.discard()`; it clears `_changes` wholesale).
3. **Kanban**: `moveRecord` is overridden on a `DynamicGroupList` subclass; the wizard
   is awaited *before* `super.moveRecord`. Cancel returns early (nothing mutated yet).
   Confirm temporarily wraps `record.update` to inject `stage_note` into the update
   `super.moveRecord` performs, so the list bookkeeping and resequence still run and
   the note rides the same write. Patching `record.update` is the same pattern
   enterprise uses in `hr_payroll/static/src/js/payslip_line_one2many.js`. Do not
   pre-set `record._changes.stage_note` instead: a failed save restores
   `initialChanges` which would keep the stale note and post it on the next save.

`changes.stage_id` in the form is a **scalar id** (`_formatServerValue` unwraps
many2one), whereas `targetGroup.value` is used in the kanban. Do not assume a pair.

### Verified

- `get_combined_arch()` on both the form and the kanban returns
  `js_class=helpdesk_ticket_stage_note_form|_kanban` and contains `stage_note`.
- Assets bundle all four JS files plus the QWeb template.
- `web_save({stage_id, stage_note}, {stage_id: {}, stage_note: {}})` on `17.0`
  changed the stage and posted exactly one `mail.mt_note`; `stage_note` stayed
  non-stored. This is what surfaced the compute bug above.
- `node --check` on all four JS files, `xmllint` on all three XML files.
- `pre-commit` clean except `manifest-version-format`, a repo-wide false positive
  (`.pylintrc` pins `18.0`, every module here is `17.0.x`; `helpdesk_ticket_pureict`
  triggers it too). Do not "fix" that.

### NOT verified — this is the main open item

The browser interaction was never driven in a real browser: snap Chromium will not
start in this environment and no chromedriver is on PATH. Still to confirm by hand:

1. Form: stage change opens the wizard; cancel leaves stage and chatter untouched and
   **retains other unsaved edits**.
2. Form: confirm changes stage and adds exactly one `mail.mt_note` in the same save.
3. Kanban: drag to another column opens the wizard; cancel keeps the card put.
4. Kanban: confirm moves the card and posts the note.
5. Unrelated field save: no wizard, no message.
6. `stage_note` never stored on `helpdesk.ticket`.

### Environment traps you WILL hit

- **`addons/helpdesk` is not in `.gitmodules`**, so `get-addons-path` omits it. The
  author's server (`--addons-path` from `.gitmodules`) therefore has no
  `helpdesk_ticket_stage_note` in its registry. Symptom: every `helpdesk.ticket`
  kanban dies with `ValueError: can only parse strings` from
  `ir_ui_view._combine`, because the inherited view reads `arch = False`. Diagnosed
  by `helpdesk.ticket.stage.note.wizard` raising "model does not exist" on the live
  server while the DB said `installed`.
- **The module is currently uninstalled from `17.0`** to restore the kanban. Any
  reinstall must use the addons path:

  ```bash
  cd /home/laurens/Odoo-Build
  ODOO_ADDONS_PATH=addons/helpdesk ./task init-module 17.0 addons/helpdesk/helpdesk_ticket_stage_note
  ```

  and the server must be (re)started with `addons/helpdesk` in `--addons-path`,
  otherwise the same crash returns.
- A headless `odoo` shell ignores `--no-http` races and may log `OSError: address in
  use`; harmless.
- `task docs` regenerates `README.md` at the repo root and rewrites the module table,
  which is why `README.md` shows as modified.

### Open questions for the author

- Add `addons/helpdesk` to `.gitmodules` so the addons path picks it up permanently?
  Not done — it is a repo-config change outside this module.
- Author asked to delete unit tests; done. Do not reintroduce them without asking.

@Clanker If author confirms results set frontmatter state to completed, otherwise to aborted. Update date, harness, provider and model. If you have access to session info update token count. Finally, update the changelog with the most important changes.
