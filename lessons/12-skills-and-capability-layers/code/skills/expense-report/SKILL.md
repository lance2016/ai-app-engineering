---
name: expense-report
description: Check an expense list against the company travel policy and produce an approval summary. Use when the user asks whether expenses are reimbursable or wants an expense report reviewed.
version: 0.9.0
allowed-tools: search_notes, read_file
---

# Expense report review

## When to use
The user gives a list of expenses (amount, category, date) and wants to know what is reimbursable.

## Procedure
1. Load `references/policy.md` for the current limits. Never rely on remembered limits.
2. For each line item, mark: approved / needs receipt / over limit / not covered.
3. Sum approved amounts. Flag anything over limit with the limit that applies.

## Output format
A table with columns: item, amount, category, verdict, note.
