---
description: "Use when starting or resuming work on the bookkeeping repo, rebuilding context, or planning the next validated change."
---

MASTER RESTART PROMPT V1: BOOKKEEPING-NL

Use this at the start of any new bookkeeping session.

Mode
- Build

Program
- bookkeeping-nl

Primary goal
- Evolve the bookkeeping application safely while preserving data integrity and clear separation between backend, frontend, and exports.

Current known baseline
- Project location: Dev/Private/Bookkeeping/bookkeeping-nl
- Local repository is the source of truth.
- App structure includes backend, frontend, scripts, tests, docs, config, and data-related folders.
- Prefer tested, incremental changes.

Execution protocol for this session
1. Summarize current state from the code and recent changes.
2. Propose a short plan with small steps.
3. Implement one step at a time.
4. Validate after each logical step.
5. End with residual risks and next actions.

Mandatory self-update block
At end of each meaningful session, update this file:
1. Completed in this session
- [bullet list]
2. Validation performed
- [tests, lint, diagnostics, manual checks]
3. New constraints or assumptions
- [bullet list]
4. Next best 3 actions
- [numbered list]