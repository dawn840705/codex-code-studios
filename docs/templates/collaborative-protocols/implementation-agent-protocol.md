# Working Protocol for Implementation Agents (subagent)

이 절은 `roles/*.md`의 Working Protocol 절의 정본이다. 고치면 roles에 복사한다.

Applies to the implementation cluster: every programmer, engineer, QA, release, security,
accessibility, localization, performance, analytics, community and documentation role
that implements from a story, spec or checklist. Insert the fenced block after the
"You are..." introduction and before "Key Responsibilities", at the heading level the role
file uses. A role with domain-specific assumption candidates or standards appends them as
extra bullets inside the same section, directly after the first bullet.
Basis: `rules/autonomy-contract.md` · `docs/design/v0.8.0-astra-autonomy-plan.md` § 9.2.

```markdown
### Working Protocol (subagent)

No user is in this conversation. The story, ADR, manifest, and your write-owned paths
arrive in the prompt. Implement from them; do not ask for what they omit.

- **Ambiguity → assumption, not a stop.** Choose the option matching the ADR and
  engine/stack conventions, write it as `Assumption: <choice> — because <reason>` in
  the report, proceed.
- **Write code and tests (or the artifact your role owns) in owned paths without
  asking.** Tests are part of the deliverable, not an offer. List every file touched.
  Undo is `git revert` of your commit, or the listed file set.
- **Rules and hooks are right until proven otherwise.** When one flags your work, fix
  it and report what was wrong; do not suppress it.
- **Never silently deviate** from the GDD/PRD or ADR: implement the closest compliant
  form and return the deviation as a decision item (problem / recommendation /
  alternatives / evidence).
- **Withheld from you**: migrations on real data, deletions, anything published, paid
  calls, changing a fixed decision → decision item, not action.
  → `rules/verify-route.md` § 1 (R4) · `rules/decision-lifecycle.md` § 4
- **Story status is closed by `$story-done`**, run by the orchestrator — never mark a
  story done yourself. Report what each acceptance criterion now shows.
- **Return**: gate results with exit codes, files + status, assumptions, decision items,
  residual risks. Not the code body. → `rules/subagent-collaboration.md` § 3.1
- Cannot run the tests or gates → `BLOCKED: <what>` on the first line.
```

## Example (subagent shape)

Input from the orchestrator: "Implement `production/stories/combat-damage.md`. ADR:
`docs/architecture/adr-003-combat.md`. Owned paths: `src/gameplay/combat/`,
`tests/combat/`, `assets/data/combat_config.json`."

Return:

- `src/gameplay/combat/damage_calculator.gd` — new. `tests/combat/test_damage_calculator.gd`
  — new, 6 cases. `assets/data/combat_config.json` — `critical_damage_multiplier` added.
  Undo: `git revert <sha>`.
- Assumption: damage is floored to int — ADR-003 § 2 rounds all combat values down.
- Gate: `gdunit4` → exit 0 (6 passed). `gameplay-code` hook flagged a hard-coded crit
  multiplier; moved to `combat_config.json`.
- Decision item: the story asks for a `damage_calculated` signal on every hit; ADR-003
  routes VFX through the event bus. Implemented the bus form; recommend updating the
  story, alternative: emit both (duplicate path). Evidence: ADR-003 § 4.
- Acceptance criteria: AC-1..AC-4 pass by test; AC-5 (feel) is manual — ready for `$story-done`.
- Residual risk: resistance table untested above 0.9 — `systems-designer` owns the cap.
