This repository contains the bookkeeping application.

- Treat the local repository as the source of truth.
- Keep backend, frontend, scripts, tests, and docs aligned when making changes.
- Prefer small, validated changes over large refactors.
- Preserve data safety and avoid committing generated or live data by accident.
- After a meaningful session, update the restart prompt in `.github/prompts/10-master-restart.prompt.md`.