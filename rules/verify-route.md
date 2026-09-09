# Verify Route — Routing the *Checking*, Not the Making

**Global rule. Applies to every project and every domain.**

[`route-hint.md`](route-hint.md) routes **production**: how many agents to spawn
for the work. It says nothing about **verification**, and so verification has no
routing at all — it runs at whatever weight the skill happens to hardcode.

That produces two failures at once, in opposite directions:

- A typo fix in a comment pulls the full `$team-qa` fan-out, because that is what
  the sprint loop says to run.
- An irreversible change — a data migration, a published release, a deleted
  system — passes on a single `$smoke-check`, because nothing said to do more.

The bottleneck in an agent workflow is not generation. It is checking. So the
expensive checks have to be spent where the risk is, and that requires the same
kind of explicit route decision production already gets.

---

## § 1 — Route by reversibility, not by importance

"Important" is a feeling and it inflates. **Reversibility is a property of the
change** and you can state it in one sentence: *if this is wrong, what does it
take to undo?*

| Risk | Test — "if this is wrong…" | Verifier | Automatic? |
|---|---|---|---|
| **R1 low** | one edit undoes it, nobody saw it | the deterministic gate that already covers the file | ✅ |
| **R2 medium** | a revert undoes it, contained to this repo | gates + `$code-review` or `$smoke-check` | ✅ |
| **R3 high** | undoing needs coordination, migration, or a re-release | gates + a **separate** reviewing subagent + `$gate-check` | ✅ report the route, then proceed (no wait) |
| **R4 critical** | cannot be undone, or undoing costs users something | everything in R3 **and a human decision** | ❌ **never runs unattended** |

**R4 examples**: schema migrations against real data, deletions of a system or
its history, anything published to users (release, patch notes, store build),
credential or permission changes, money.

Note the shape of the table: the verifier column grows, and only the *last row*
takes the decision away from the agent. Escalation is not "be more careful", it
is "add this named check".

---

## § 2 — Escalate on a signal; never quietly de-escalate

Move **up** a level when any of these is true. One is enough:

- the change touches a boundary you cannot see the far side of
- a gate already failed once and this is rework ([`self-loop.md`](self-loop.md))
- the blast radius is other people's work, not just this repo
- you are unsure which level applies

**Uncertainty escalates.** That is the asymmetry: guessing high costs one extra
check, guessing low costs whatever the change breaks.

Moving **down** is a different act and needs a reason recorded in the output —
`R3 → R2: migration is additive, no existing column is touched`. An unexplained
de-escalation is indistinguishable from having skipped the check.

---

## § 3 — The verdict comes from the gate, not the verifier's prose

Everything in [`docs/deterministic-gates.md`](../docs/deterministic-gates.md)
applies here without exception:

- **The exit code is the verdict.** A reviewing agent that says "looks good"
  next to `pytest → exit 1` has not overturned anything.
- **A gate that could not run (`3`) is not a gate that passed.** At R3 and R4,
  an unrunnable gate is itself an escalation trigger — you now know less than
  you planned to.
- **Name the deciding gate** in the report: `verify_policy.py → exit 2 (P2)`.
- Machine-readable form: every gate emits the shared 4-field envelope under
  `--json` (`scripts/gate_report.py`), so a caller reads `status` instead of
  parsing prose.

---

## § 4 — At R3 and above, the reviewer is not the author

An agent asked to check its own output defends it. That is not dishonesty, it is
the same context producing the same conclusions twice.

At **R3+**, verification goes to a **separate subagent** that receives:

- the final state (files, diff, gate output) — **not** the narrative of how it
  was produced
- the criteria, stated independently
- an explicit prohibition on editing anything

It returns defect tickets, not a score
([`self-loop.md`](self-loop.md) § 2.1) — and per
[`subagent-collaboration.md`](subagent-collaboration.md) § 3.1 it returns them
as findings, not as a retelling of its search.

---

## § 5 — Report the route, always

One line, in the output, whatever the level:

```
verify: R2 (revert undoes it, contained to this repo)
  → pytest tests/ exit 0 · verify_policy.py exit 0 · $code-review PASS
```

The route is a decision the user is entitled to see and disagree with. An
unstated route is unreviewable, and the failure this rule exists to prevent —
an R4 change checked as if it were R1 — is invisible precisely when nobody wrote
the level down.

---

## § 6 — Anti-patterns

- ❌ **`$team-qa` on a one-line fix** — that is R1; the file's own gate covers it
- ❌ **`$smoke-check` alone on a migration** — R4 needs a human, not a smoke test
- ❌ **Escalating because the task sounds important** — use reversibility (§ 1)
- ❌ **De-escalating silently** — record the reason or stay at the higher level
- ❌ **The author agent grading its own work at R3+** — § 4
- ❌ **Reading `exit 3` as a pass** — at R3+ it is an escalation trigger
- ❌ **Running R4 unattended because the gates were green** — green gates are the
  precondition for asking, not a substitute for the answer

---

## Related

- [`route-hint.md`](route-hint.md) — routes production; this file routes checking.
  A heavy production route does **not** imply R3, and R3 does not imply heavy —
  a one-line change to a published config is R4 on the light route.
- [`self-loop.md`](self-loop.md) — what happens after a verifier says FAIL
- [`docs/deterministic-gates.md`](../docs/deterministic-gates.md) — the exit-code
  contract and the shared report envelope
- [`subagent-collaboration.md`](subagent-collaboration.md) — how to brief the
  separate reviewer at R3+
