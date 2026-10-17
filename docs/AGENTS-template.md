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

- Read the handoff's linked instructions before acting; follow
  `rules/work-records.md` in the Code Studios source for shared record placement.
- Shared memory lives in repository files, never agent auto-memory. Put standing
  rules here, decisions in decision records, requests in the project inbox,
  status in the status document, and other knowledge behind a shared index.
- If both runtimes work here, keep `CLAUDE.md` aligned with these agreements or
  link both entry points to the same shared rules. Recommend disabling automatic
  memory where supported; check the runtime's setting syntax first.
- Before implementation, establish purpose, expected behavior, and acceptance
  criteria from the design, code, and records. Examine failure cases and
  alternatives; state material assumptions. Resolve routine choices within
  scope and ask only about consequential unknowns that evidence cannot settle.
- Run relevant tests after code changes. For changed gameplay/UI, also exercise
  the real user path and inspect the screen/behavior where available. Report
  implementation, automated checks, execution, and human acceptance separately;
  keep missing verification explicit and honor the project's human gates.
- Turn verified recurring mistakes into concise prevention rules linked to the
  evidence. Update matching rules instead of accumulating duplicates; retain
  detailed lesson history. Follow `rules/lesson-capture.md` in the source checkout.
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
