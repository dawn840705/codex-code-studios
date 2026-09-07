# Project AGENTS.md template

Copy the contents below into a consumer project's root `AGENTS.md` and tailor it
to the repository. Commit shared team rules; keep machine-specific secrets and
credentials out of this file.

```markdown
# Project guide

## Product and stack

- Track: game | product
- Engine/framework and pinned version:
- Target platforms:
- Architecture source of truth:

## Working agreements

- Run the relevant tests after code changes.
- Preserve existing user changes and avoid destructive cleanup.
- Record major technical choices as ADRs.
- Keep `production/session-state/active.md` current during multi-session work.

## Code Studios policy feedback

- Source checkout (configure for this project):
- When a confirmed working agreement or verified prevention measure also applies
  to other projects, follow `docs/policy-updates.md` in the source checkout and
  update the relevant rule, skill, or template during task closeout.
- Keep product-specific decisions here. Record the source commit and distinguish
  source changes from the plugin version actually installed.

## Local commands

- Build:
- Unit tests:
- Integration tests:
- Lint/format:

## Communication

- Lead with outcomes and verification evidence.
- Surface decisions that require product or design authority.
```

Code Studios stores engine and naming preferences separately in
`.codex/studio/technical-preferences.md`; `$setup-engine` can create it.
