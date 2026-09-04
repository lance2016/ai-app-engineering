---
name: expense-report
description: Check an expense list against the company travel policy and produce an approval summary. Use only when the user asks whether expenses are reimbursable or wants an expense report reviewed.
version: 1.0.0
allowed-tools: read_skill_reference, search_docs
---

# Expense report review

## When to use
The user gives a list of expenses (amount, category, date) and wants to know what is reimbursable. Do not use for general travel questions.

## Procedure
1. Call `read_skill_reference(skill="expense-report", path="references/policy.md")` for the current limits. Never rely on remembered limits.
2. For each line item, mark: approved / needs receipt / over limit / not covered.
3. Sum approved amounts. Flag anything over limit with the limit that applies.

## Output format
A table with columns: item, amount, category, verdict, note. End with the approved total.
