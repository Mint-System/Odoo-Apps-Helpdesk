---
commit_ref: 32db19e82d102268e4372b3516948e89e97431eb
title: "research dialog options"
author: "laurens kooijman <laurenskooijman@gmail.com>"
session_id: 01a2177e-fb70-73fe-8a46-8b2ff1f7809c
action: execute
state: completed
date_completed: 2026-11-26
harness: pi
provider: mistral
model: deepseek-v4-1-flash-1017
input_tokens: 257603
output_tokens: 40876
---

# research dialog options

Note: @Clanker refers to the "ai agent" (you) who is working on this prompt file.

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` to get an understanding of the project
- Read task section and prepare a list of todos
- Update the todo list while working on task

@Clanker When task is completed set frontmatter state to review. If you have access to session info add token count and session id. Prompt the author to verify the results.

## Task

Do not change anything during this prompt. This prompt is only to research the possibilities for creating a module.

The module I am creating should open a dialog when changing the stage of a helpdesk ticket, either in the ticket or by draggin in the kanban view. The dialog should be able to cancel the state change.

Look into odoo modules in the folders `odoo-build/addons/*/` `odoo-build/odoo` `odoo-build/enterprise` and report on any
module that uses a wizard or calls a dialog in a write method.

Look for modules that have the described use case. Report back on which modules. I want to use an existing code example for my module.

Using the information that you searched above, suggest a method for implementing the dialog for stage changes that is based on one or multiple methods that is already present in Odoo.


## Worklog

Research only — no files were changed.

### 1. Key technical constraint

A wizard **cannot** be opened from a Python `write()` method. The ORM discards its
return value, and `web/models/models.py:90` (`web_save`) calls `self.write(vals)` and
then returns `web_read(...)` — the write return value never reaches the client. Any
pattern that opens a dialog on save therefore has to live in JavaScript, or has to
block with an exception (server) and let the dialog be the error dialog.

So there are exactly two viable mechanisms:

| Mechanism | Trigger | Can cancel | Dialog type |
|---|---|---|---|
| `onWillSaveRecord` returning `false` (or a Promise resolving `false`) | Form and List view save | Yes, before the RPC | Real dialog / wizard (`target: 'new'`) |
| Python `raise UserError/ValidationError` from `write`/`@api.constrains` | Any write, incl. kanban drag | Yes, RPC aborts and kanban reverts | Error dialog only (message, no inputs) |

Note that Odoo **only wires `onWillSaveRecord` in the Form and List controllers**
(`form_controller.js:417`, `list_controller.js:333`). The Kanban controller only wires
`onRecordSaved` (`kanban_controller.js:322-325`). So `onWillSaveRecord` is **not
available on kanban**. The kanban interception point is `moveRecord` on the model.

### 2. Modules that call a dialog from a save / write path

Best references, in order of usefulness:

1. **`odoo/addons/account/static/src/components/currency_form/form_controller.js`** —
   *the closest match to the requested use case.* A `FormController` that overrides
   `onWillSaveRecord(record)`, shows a `ConfirmationDialog`, resolves `true` on confirm,
   and on cancel calls `record.discard()` and resolves `false` → the save is aborted.
   ~30 lines, no Python side needed. Wired via a new view `js_class`.
   **Not available in 17.0** — see `### Works in Odoo 17.0?` for the substitutes.

2. **`odoo/addons/crm/static/src/views/crm_kanban/crm_kanban_model.js`** —
   *the kanban-drag counterpart.* Subclasses `RelationalModel.DynamicGroupList` and
   overrides `async moveRecord(dataRecordId, dataGroupId, refId, targetGroupId)`. It
   calls `super.moveRecord(...)` and then, if grouped by `stage_id`, opens a dialog
   (`checkRainbowmanMessage` → `effect` service). Because it runs **around** `super`,
   an `await dialogs.confirm()` **before** `super.moveRecord(...)` cancels the move before
   anything is mutated. This is the supported hook for kanban drag-and-drop.

3. **`odoo/addons/hr_recruitment/static/src/views/recruitment_kanban_view.js`** —
   `KanbanRenderer` subclass overriding `archiveRecord` with a `ConfirmationDialog`
   before mutating. Shows the renderer-level override idiom.

4. **`odoo/addons/hr/static/src/views/preferences_form_view.js`** —
   minimal `onWillSaveRecord` override that inspects `changes` (the dict of modified
   fields). Good template for "only act when `stage_id` is in `changes`".

5. **`enterprise/helpdesk/static/src/views/helpdesk_team_form/helpdesk_team_form_controller.js`** —
   the same-app precedent: `async onWillSaveRecord(record)` that inspects `record.data`
   (the `changes` argument is not passed by this override in 17.0), RPCs to Python, and
   returns `res`. Confirms the pattern is idiomatic in this exact codebase.

6. **`odoo/addons/mail/static/src/chatter/web/form_controller.js`**,
   **`enterprise/knowledge/.../knowledge_controller.js`**,
   **`enterprise/mrp_maintenance/.../maintenance_request_form_view.js`**,
   **`enterprise/pos_self_order_iot/.../iot_box_form.js`** — further
   `onWillSaveRecord`/`onRecordSaved` overrides, all dialogs/actions from the save phase.

7. **`oca/helpdesk/helpdesk_mgmt_stage_validation`** — the *server-side* option for this
   exact problem: `@api.constrains("stage_id")` raising `ValidationError` when required
   fields are empty. Works for both form save and kanban drag, with no JS at all. The
   kanban drag is reverted automatically (`dynamic_group_list.js:135-142` calls
   `revert()` and rethrows → the global error service shows the message). Downside: the
   user gets a plain error dialog, cannot fill in the missing data in the dialog.

8. **`odoo/addons/hr_presence/models/hr_employee.py:109`** — example of the
   `{'type': 'ir.actions.act_window', 'target': 'new'}` dict returned from an `action_*`
   method (not from `write`), i.e. how a Python wizard is opened.

### 3. Recommended approach for the stage-change dialog

Use a **JS view-level dialog that cancels the write**, mirroring `account`
(currency form) for the form view and `crm` (kanban model) for the kanban drag, and
put the wizard itself in Python so the dialog is a real form (`target: 'new'`), not a
bare confirmation.

**A. Form view (stage statusbar)**
- New view record via a `js_class="helpdesk_ticket_form_dialog"` extending
  `helpdesk`'s form view, registered in `registry.category("views")`.
- Controller subclassing `FormController` with
  `async onWillSaveRecord(record, changes)`:
  - if `"stage_id" in changes` and the new stage requires info → `await` the wizard
    through `this.action.doAction({... wizard ..., target: "new"})`, or use
    `this.dialog.add(...)`;
  - on confirm, write the wizard's values onto the record
    (`record.update({...})` — not `record.save()`, to stay inside the pending save)
    and `return true`;
  - on cancel, `return false` → the save is aborted, the stage is not changed.
- Copy the resolve/reject shape from `account/.../currency_form/form_controller.js`
  (Odoo 19) or `odoo/addons/hr/static/src/views/profile_form_view.js` (17.0).

**B. Kanban view (drag between stage columns)**
- Subclass the existing `helpdesk_ticket_kanban` view (it is already
  `js_class="helpdesk_ticket_kanban"` with `default_group_by="stage_id"`,
  `helpdesk_ticket_views.xml:304`) — or register a `Model` on that view if it may be
  edited.
- Subclass `RelationalModel.DynamicGroupList`, override `moveRecord`:
  ```js
  async moveRecord(...args) {
      const [dataRecordId, dataGroupId, , targetGroupId] = args;
      if (dataGroupId !== targetGroupId && /* groupByField.name === 'stage_id' */) {
          const ok = await this._confirmStageChange(dataRecordId, targetGroupId);
          if (!ok) {
              return; // cancels: nothing was mutated yet
          }
      }
      return super.moveRecord(...args);
  }
  ```
  The `return;` before `super` is the cancellation — `moveRecord` only mutates the
  groups inside `super` (`dynamic_group_list.js:105-140`), so returning early leaves the
  kanban untouched. Follow `crm_kanban_model.js` for the class/`Model` wiring.
- Assign via `CrmKanbanModel.DynamicGroupList = ...` style
  (`CrmKanbanModel.DynamicGroupList = CrmKanbanDynamicGroupList;`).

**C. Python side**
- A `TransientModel` wizard (e.g. `helpdesk.ticket.stage.change.wizard`) with the extra
  fields the stage needs, exposed with `target: "new"` and a method
  `action_confirm()` that writes the ticket and returns
  `{"type": "ir.actions.act_window_close"}`.
- Keep a `write()` guard (or `@api.constrains("stage_id")`, as
  `helpdesk_mgmt_stage_validation` does) so the rule is also enforced for imports,
  RPC and multi-record writes that bypass the JS view. This is defence in depth: the JS
  dialog is the UX, the Python guard is the invariant.

**Why not a pure server-side wizard:** a `write()` cannot return an action, and
`@api.onchange`/`compute` cannot cancel a committed write. Pure server-side can only
block with an error — it can never collect extra data, which is the whole point of the
dialog.

**Why not patch `sortRecordDrop` in the renderer:** it works, but the model-level
`moveRecord` override is the documented extension point already used by `crm`, and it
keeps the renderer free of business logic.

### 4. Caveats to verify while implementing
- Quick-create and the "+ stage" header may also move records; check
  `helpdesk_ticket_kanban_header.js` and the kanban view definition for other paths.
  (17.0 has no `rotting_kanban_view`; the header is `helpdesk_ticket_kanban_header.js`.)
- Multi-record edits (`multi_edit="1"` is set on the list view,
  `helpdesk_ticket_views.xml:215`) will fire `onWillSaveRecord` per record — decide
  whether to allow or block those.
- `record.update()` inside `onWillSaveRecord` may re-trigger validation; use
  `record.update(..., { save: false })` semantics or the wizard RPC instead of a nested
  save.

### 5. Follow-up: is a post-write dialog easier for a chatter message?

*Answer: yes for the dialog itself, no for the outcome — it silently loses the message.*

The requirement is now to post a `message_post` in the chatter with text entered in the
dialog. That changes the trade-off:

| | pre-write (`onWillSaveRecord`) | post-write (`onRecordSaved`) |
|---|---|---|
| Available on form | yes | yes |
| Available on kanban drag | **no** (kanban wires only `onRecordSaved`) | yes |
| Can cancel | yes (`return false`) | **no — already committed** |
| Message lost if user closes tab / hits Cancel | no | **yes** |

`onRecordSaved(record, changes)` is the easiest hook to *reach*: it exists on form, list
and kanban (`kanban_controller.js:325`, `form_controller.js:371`,
`list_controller.js:227`) and receives `changes` (`record.js:1205`), so detecting
`"stage_id" in changes` is trivial. Precedents:
`enterprise/planning/.../planning_form_view.js` (`onRecordSaved` + dialogs),
`odoo/addons/hr/.../preferences_form_view.js`, `odoo/addons/project/.../project_project_form_controller.js`.

**But it cannot cancel, and it cannot roll back.** Once the stage is written, the
dialog can only *append* a note. If the user dismisses it, or the request fails, the
stage has changed with no explanation in the chatter — the exact case the requirement
wants to prevent. Also `onRecordSaved` fires for *every* save that touched `stage_id`,
including RPC, import and the kanban drag, so a modal appearing "after the fact" on
those paths is a UX regression.

**Recommended: keep the dialog pre-write, post the message server-side.**
- The dialog stays in `onWillSaveRecord` (form) / `moveRecord` (kanban) so it can
  cancel, as described in section 3.
- The wizard's `action_confirm()` does both in one transaction:
  `ticket.write(stage/vals)` **and** `ticket.message_post(body=..., subtype_xmlid="mail.mt_note")`.
  One RPC, atomically consistent: no stage change without a note, no note without a
  stage change.
- `stage_id` already has `tracking=1` (`helpdesk_ticket.py:114-119`), so the stage
  change itself is already logged; the wizard message is the human reason, posted as
  `mail.mt_note` (internal note) right after it. See
  `oca/helpdesk/helpdesk_mgmt_crm/wizard/helpdesk_ticket_create_lead.py:65` and
  `oca/helpdesk/helpdesk_mgmt_merge/wizard/helpdesk_ticket_merge.py:147` for the
  `wizard → ticket.message_post(...)` idiom.
- If the extra text should be visible *before* the stage change commits, an
  `@api.constrains` on `stage_id` can require a non-empty reason (section 2.7 pattern).

**Middle ground, if the pre-write plumbing feels heavy:** ship the post-write version
first as a prototype (it is genuinely less code — one `onRecordSaved` override, no
`moveRecord` subclass, no view re-registration for kanban), and accept that the note
is best-effort. Then move the trigger to pre-write once the UX matters. The Python
wizard (`action_confirm` doing `write` + `message_post`) is identical in both variants,
so that part is throwaway-free.

### Summary

There is no Odoo core module that opens a *data-collecting wizard* from a stage change.
The two supported building blocks exist separately and are both used in core:
`onWillSaveRecord` returning `false` (account currency form, hr preferences, helpdesk
team form) for save-time cancellation, and a `moveRecord` override on the kanban model
(crm) for drag-time interception. Combining these with a Python `TransientModel`
wizard, plus an `@api.constrains` guard for non-UI writes, gives the requested
behaviour with the least custom code. The nearest single-file example to copy is
`odoo/addons/account/static/src/components/currency_form/form_controller.js` (19.0) or
`odoo/addons/hr/static/src/views/profile_form_view.js` (17.0, the current target).

## Specification

**Module:** `helpdesk_stage_note` (new, in `addons/helpdesk/`), depends on `helpdesk`.

**Purpose:** When a `helpdesk.ticket` changes stage, require the user to enter a note
that is posted to the ticket chatter, before the stage is written. The interaction is
cancellable: no stage change means no note, no note means no stage change.

### Behaviour

| Actor | Expected |
|---|---|
| Change stage in form statusbar | Wizard opens before write. Confirm → stage + note committed. Cancel → nothing changes. |
| Drag card to another stage column | Same wizard, same guarantees. Cancel → card snaps back. |
| Confirm / cancel | Both must be reachable; `Esc` and the X count as cancel. |
| Non-UI write (import, RPC, mass edit) | No wizard (impossible by design); stage change proceeds without a note. |
| Stage is unchanged by the save | No wizard. |

### Data model

`helpdesk.ticket.stage.note.wizard` (`TransientModel`):

| Field | Type | Notes |
|---|---|---|
| `ticket_id` | Many2one `helpdesk.ticket`, required, ondelete cascade | |
| `stage_id` | Many2one `helpdesk.stage`, read-only display | Target stage, shown for context |
| `note` | Text, required | Chatter message body |

The wizard is **passive**: it collects the note and returns it to the caller. It does not
write the ticket. `action_confirm()` returns the note so the JS caller can apply it
(`stage_note` on the form record, or alongside the group-by value on kanban).

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

One RPC, one transaction: the note cannot be persisted without the stage change, and
`stage_note` is never stored on the ticket (transient-by-convention).

### Client

**Decision — the form performs the write.** The wizard never writes `stage_id`. It only
collects the note. The form's own save writes stage + note together.

Rationale: reverting the statusbar after a cancelled wizard is only possible via
`record.discard()` in 17.0 — there is **no per-field revert** on `RelationalRecord`
(grep for `revert` in `record.js` yields only an unrelated comment), and `_discard()`
resets `data` from `_values` and clears `_changes`, i.e. it throws away **every other
unsaved edit in the form** (`record.js:523-544`). Having the wizard write would therefore
make cancel destroy unrelated user input. Letting the form write means a cancelled
wizard simply returns `false` from `onWillSaveRecord`, which makes `record._save()`
return `false` before the RPC (`record.js:1040-1043`) — no write, no local change to
revert, because the statusbar value is only ever a pending `_changes` entry.

**Form.** Subclass helpdesk's form view via a new `js_class` (`helpdesk_ticket_form`
stays untouched). `onWillSaveRecord(record, changes)`:

1. If `"stage_id" not in changes`, `return true` immediately — no wizard.
2. Open the wizard (`ir.actions.act_window`, `target: "new"`) and await it. Cancel/close
   → `return false`; the statusbar resets on the next render and nothing is written.
3. Confirm → the wizard returns its `note`. Stash it on the controller
   (`this.stageNote = note`) together with the target `stage_id`, `return true`, and let
   the normal form save proceed.
4. In `onRecordSaved(record, changes)`, if `this.stageNote` is set, call the server to
   post it (`record.model.orm.call("helpdesk.ticket", "message_post", ...)`) and clear
   the stash.

Step 4 is the one weak point: `onRecordSaved` runs after the commit, so a failed
`message_post` leaves a stage change without a note. Close that gap by having the
**Python side** post the note instead: write the note into a transient field
(`stage_note`) that the ticket's `write()` swaps for a `message_post` and drops before
`super()`. That keeps one RPC, one transaction, and no JS-side failure window:

```python
class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    stage_note = fields.Text(store=False, compute=lambda self: None)

    def write(self, vals):
        note = vals.pop("stage_note", False)
        res = super().write(vals)
        if note:
            self.message_post(body=note, subtype_xmlid="mail.mt_note")
        return res
```

The wizard's confirm sets `stage_note` on the form record (`record.update({"stage_note":
note})`) and closes; the user's own save then persists both. Preferred over step 4 when
the note must be guaranteed.

**Kanban.** Subclass the existing `helpdesk_ticket_kanban` view with a
`RelationalModel.DynamicGroupList` subclass overriding `moveRecord`. If the source and
target group differ and the view is grouped by `stage_id`, open the wizard **before**
`super.moveRecord(...)`:

- Cancel → `return` early. Nothing is mutated yet, and 17.0's `moveRecord` additionally
  reverts if `record.update()` returns falsy (`dynamic_group_list.js:118-131`).
- Confirm → write `stage_note` alongside the group-by value so the same Python hook
  posts it: `record.update({stage_id, stage_note: note}, { save: true })`.

Follow `odoo/addons/crm/.../crm_kanban_model.js` for the class/`Model` wiring. No
revert is needed on the kanban side because `_removeRecords`/`_addRecord` only run
inside `super`; 17.0 also reverts explicitly when `record.update()` returns falsy (the
`revert()` helper at `dynamic_group_list.js:118-131`).

**Why not post-write.** `onRecordSaved` is easier (wired on form, list and kanban) but
runs after the commit: a dismissed dialog leaves a stage change with no note. Rejected.

**Why not server-side only.** A Python `write()` cannot return an action
(`web_save` drops it), and an `@api.constrains` can only block with an error dialog,
not collect text. Rejected as the primary mechanism.

### Out of scope
- Blocking non-UI writes; they proceed silently (dokumented limitation).
- Stage-specific required fields; that is what `helpdesk_mgmt_stage_validation` does.
- Portal/website ticket views.

### Acceptance
1. Form: changing stage opens the wizard; cancel leaves stage and chatter unmodified, and
   any other unsaved field edits in the form are **retained**.
2. Form: confirm changes stage and adds exactly one `mail.mt_note` message in the same
   save (one `web_save` call carrying both `stage_id` and `stage_note`).
3. Kanban: drag to another column opens the wizard; cancel keeps the card in its column.
4. Kanban: confirm moves the card and posts the note.
5. Saving an unrelated field posts no message and opens no wizard.
6. `stage_note` is never stored on `helpdesk.ticket` (no column is written).

### Works in Odoo 17.0?

Yes — verified against the 17.0 sources in this checkout (`release.py:
version_info = (17, 0, 0, FINAL, 0, '')`). Both mechanisms exist unchanged:

| API | 17.0 location | Status |
|---|---|---|
| `onWillSaveRecord(record, changes)`, `return false` cancels | `web/static/src/model/relational_model/record.js:1040`; `form_controller.js:326` | present (framework passes `changes`; view overrides may omit it) |
| Kanban wires only `onRecordSaved` | `kanban_controller.js` | present (same gap) |
| `DynamicGroupList.moveRecord` | `relational_model/dynamic_group_list.js:88` | present |
| `crm_kanban_model.js` `moveRecord` override | `crm/static/src/views/crm_kanban/crm_kanban_model.js` | byte-identical to 19.0 |
| `helpdesk_ticket_kanban` js_class, `default_group_by="stage_id"` | `enterprise/helpdesk/views/helpdesk_ticket_views.xml:283` | present |
| `ir.actions.act_window_close` | `odoo/addons/payment_stripe/models/payment_provider.py:149` | present |

Differences that matter for the implementation:

1. **`/** @odoo-module **/` header is required** at the top of every 17.0 JS file;
   without it the module is silently not registered.
2. **The `account` currency-form reference does not exist in 17.0.** Use instead
   `odoo/addons/hr/static/src/views/profile_form_view.js` (minimal
   `onWillSaveRecord(record, changes)`) and
   `enterprise/knowledge/static/src/js/knowledge_controller.js:173` (dialog from the
   save path). `enterprise/helpdesk/.../helpdesk_team_form_controller.js:26` is
   available and is the closest same-app precedent — note that in 17.0 its override
   signature is `onWillSaveRecord(record)` and it diffs `record.data` rather than using
   `changes`. The framework itself does pass `changes` (`record.js:1040`), so the new
   controller can use `(record, changes)`.
3. **The helpdesk form has no `js_class` in 17.0** (`<form string="Helpdesk Ticket">`,
   `helpdesk_ticket_views.xml:359`). Add a new inherited view that sets
   `js_class="helpdesk_ticket_form_stage_note"` — no core view needs patching.
4. **The kanban view is plain `kanbanView`**, not `rottingKanbanView` (17.0:
   `helpdesk_ticket_kanban_view.js`). Re-register the key by spreading the existing
   `helpdeskTicketKanbanView` and overriding `Model`, so the renderer/header from
   enterprise is preserved.
5. `moveRecord` in 17.0 already reverts when `record.update()` returns falsy
   (`dynamic_group_list.js:118-128`), so a cancelled write cannot leave the card in the
   wrong column.
6. Odoo 19's `rotting_statusbar_duration` widget is `statusbar_duration` in 17.0
   (`helpdesk_ticket_views.xml:361`); the inherited view must match.

### Can this be done without JavaScript?

Partially. Three levels exist, in increasing order of fidelity:

| Option | JS | Dialog collects text | Cancel works | Notes |
|---|---|---|---|---|
| **S1.** `@api.constrains("stage_id")` raising `ValidationError` | none | **no** | yes (error dialog, write rolled back) | the `helpdesk_mgmt_stage_validation` pattern |
| **S2.** `stage_id` readonly + a button opening a Python wizard | none | **yes** | yes (dialog X / Esc) | loses statusbar click **and** kanban drag |
| **S3.** `onWillSaveRecord` / `moveRecord` (the spec above) | yes | yes | yes | cancellable **and** keeps drag/click |

**S1 — block without a dialog.** `@api.constrains("stage_id")` raising `ValidationError`
when the note is missing. Covers every write path, including kanban drag: 17.0's
`moveRecord` catches, reverts the card and rethrows (`dynamic_group_list.js:118-131`), and
the global error service shows the message. This is exactly what
`oca/helpdesk/helpdesk_mgmt_stage_validation` ships. Downside: the user can never supply
the note *in* the dialog — they are blocked, then have to edit a field and retry.
Acceptable if the note is a validation rule, not if the dialog is the intended UX.

**S2 — server-only wizard, at the cost of the kanban drag.** Set `stage_id` to
`readonly=True` (currently `readonly=False`, `helpdesk_ticket.py:114-119`) and add a
header button that opens the wizard. This satisfies "a dialog that can cancel" with zero
JS: the user types the note in a real `TransientModel` form, and closing it cancels. It
works because the client already disables both entry points for a readonly grouped
field:

- statusbar: `isDisabled: !options.clickable || dynamicInfo.readonly`
  (`web/.../fields/statusbar/statusbar_field.js:357`);
- kanban drag: `canMoveRecords` returns `false` when
  `this.props.list.fields[groupByField.name].readonly`
  (`web/.../kanban/kanban_renderer.js:216-241`).

So the stage can no longer be changed ad hoc — only through the wizard. The cost is
real: dragging cards between stage columns is the primary helpdesk interaction, and S2
removes it. `readonly` can be conditional (`readonly="<expr>"` in the view arch) to scope
the restriction to certain teams or stages.

**S3** is the only option that keeps both the drag and the collected text, which is why
it is the recommendation — about 60-80 lines of JS.

**Verdict:** if "no JavaScript" is a hard constraint, use **S2** (accept losing kanban
drag) or **S1** (accept an error dialog instead of an input dialog). If the drag must
stay and the note must be typed in the dialog, JavaScript is unavoidable: a Python
`write()` cannot return an action — `web_save` discards its return value
(`web/models/models.py:68-75` in 17.0) — and no Python hook can open a dialog from a
committed write.

### References
- Dialog + save-cancel: `odoo/addons/hr/static/src/views/profile_form_view.js`,
  `enterprise/knowledge/static/src/js/knowledge_controller.js:173`
- Kanban drag hook: `odoo/addons/crm/static/src/views/crm_kanban/crm_kanban_model.js`
- Same-app `onWillSaveRecord`: `enterprise/helpdesk/static/src/views/helpdesk_team_form/helpdesk_team_form_controller.js:26`
- `wizard -> message_post`: `oca/helpdesk/helpdesk_mgmt_merge/wizard/helpdesk_ticket_merge.py:147`

---

## Next prompt

Copy the block below into a fresh `prompt.md` to start implementation.

```markdown
---
title: "stage change note wizard"
author: "laurens kooijman <laurenskooijman@gmail.com>"
session_id:
action: execute
state: draft
date_completed: YYYY-MM-DD
harness:
provider:
model:
input_tokens:
output_tokens:
---

# stage change note wizard

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` to get an understanding of the project
- Read the `## Specification` section below and prepare a list of todos
- Update the todo list while working on task
- Use `./task generate-module-wizard` and the other `generate-module-*` commands
  instead of hand-writing module files

@Clanker When task is completed set frontmatter state to review. If you have access to
session info add token count and session id. Prompt the author to verify the results.

## Specification

**Module:** `helpdesk_stage_note` (new, in `addons/helpdesk/`), depends on `helpdesk`.

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

### Odoo 17.0 constraints (target version)

Verified against this checkout (`release.py: version_info = (17, 0, 0, FINAL, 0, '')`).
`onWillSaveRecord` (cancels on `false`), the kanban `onRecordSaved`-only gap, and
`DynamicGroupList.moveRecord` all exist unchanged. Implementation notes:

1. Every JS file needs a `/** @odoo-module **/` header, or the module is silently not
   registered.
2. The helpdesk form has **no** `js_class` in 17.0 (`helpdesk_ticket_views.xml:359`).
   Add an inherited view setting `js_class="helpdesk_ticket_form_stage_note"`.
3. The kanban view is plain `kanbanView`, not `rottingKanbanView`. Re-register the
   existing `helpdesk_ticket_kanban` key by spreading `helpdeskTicketKanbanView` and
   overriding only `Model`, so the enterprise renderer/header is preserved.
4. The statusbar widget is `statusbar_duration`, not `rotting_statusbar_duration`
   (`helpdesk_ticket_views.xml:361`).
5. `moveRecord` already reverts when `record.update()` returns falsy
   (`dynamic_group_list.js:118-128`).
6. The module's `version` must be `17.0.1.0.0`, matching the checkout and the sibling
   `helpdesk_ticket_pureict`.

### No-JavaScript fallback (only if the author rejects the JS approach)

The JS in this specification is not optional for the stated behaviour. A Python
`write()` cannot return an action (`web_save` discards it, `web/models/models.py:68-75`),
and no Python hook opens a dialog from a committed write. If JS must be avoided, stop and
ask the author to choose:

- **S1** — `@api.constrains("stage_id")` raising `ValidationError`. No dialog input; the
  user is blocked and must retry. Pattern: `oca/helpdesk/helpdesk_mgmt_stage_validation`.
- **S2** — `stage_id` readonly + header button opening the Python wizard. Real dialog
  with input, but the statusbar click and kanban drag are disabled by the client
  (`statusbar_field.js:357`; `kanban_renderer.js:216-241`).

Do not silently downgrade to S1 or S2; the acceptance criteria assume S3.

## Worklog

@Clanker Add a summary here once the task has been completed.
```

@Clanker If author confirms results set frontmatter state to completed, otherwise to aborted. Update date, harness, provider and model. If you have access to session info update token count. Finally, update the changelog with the most important changes.
