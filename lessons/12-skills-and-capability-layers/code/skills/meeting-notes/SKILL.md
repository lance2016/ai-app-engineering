---
name: meeting-notes
description: Turn a raw meeting transcript into structured notes with decisions, action items and owners. Use when the user pastes a transcript or asks to summarize a meeting.
version: 1.2.0
allowed-tools: search_notes
---

# Meeting notes

## When to use
The user provides a transcript, chat log or rough notes from a meeting and wants a clean summary.

## Procedure
1. Read the whole transcript before writing anything.
2. Extract, in this order: decisions, action items (with owner and due date if stated), open questions.
3. Keep every action item to one line: `- [ ] owner: task (due)`.
4. If an owner is not named, write `unassigned`, never guess a person.

## Output format
```
## Decisions
## Action items
## Open questions
```

## Do not
- Do not invent decisions that were only discussed.
- Do not include small talk.
