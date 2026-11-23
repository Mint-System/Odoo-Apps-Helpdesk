---
commit_ref:
title: "new module ticket pureict"
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

# new module ticket pureict

Note: @Clanker refers to the "ai agent" (you) who is working on this prompt file.

@Clanker when working on this prompt file, make sure to:

- Read the `AGENTS.md` to get an understanding of the project
- Read task section and prepare a list of todos
- Update the todo list while working on task

@Clanker When task is completed set frontmatter state to review. If you have access to session info add token count and session id. Prompt the author to verify the results.

## Task

In the premade module `helpdesk/helpdesk_ticket_pureict`, add to the module `helpdesk.ticket` the following fields with the mentioned type. Add a view to show these fields on a new page called `Change Management` with 2 columns in the order as in the list below. Add the text after "Help" as the description/help text of the field.

*column1*
change_reason - Type: Text - Help: "Beschreib kurz die Notwendigkeit"
risk - Type: Auswahl("Niedrig", "Mittel", "Hoch") - Help: "Niedrig = Probleme unwahrscheinlich, Mittel = Probleme möglich, Hoch = Probleme sehr wahrscheinlich"
impact - Type: Text - Help: "Niedrig = Keine Betriebseinschränkung, Mittel =  Geringe Betriebseinschränkung, Hoch = Erhebliche Betriebseinschränkung"

*column2*
implementation_plan - Type: Text - Help: "Beschreib kurz deine Planung"
rollback_plan - Type: Text - Help: "Beschreib kurz, wie du die Änderung rückgängig machst"
test_plan - Type: Text - Help: "Beschreib kurz die geplanten Prüfungen"
planned_execution - Type: Date/Time - Help: "Gib den geplanten Zeitpunkt der Umsetzung an"


## Worklog

@Clanker Add a summary here once the task has been completed.

@Clanker If author confirms results set frontmatter state to completed, otherwise to aborted. Update date, harness, provider and model. If you have access to session info update token count. Finally, update the changelog with the most important changes.
