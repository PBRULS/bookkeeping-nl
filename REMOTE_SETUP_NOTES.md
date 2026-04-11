Future remote setup notes

- Local repository is currently the source of truth.
- Branch name normalized to `main`.
- Old inherited `origin` remote was removed intentionally in the extracted repo copy.
- Before pushing, decide whether this extracted repo replaces the copied non-git folder as the canonical path.
- Add `origin` only after validating the extracted history and working tree.