---
name: self-loop
description: "Iterate on a deliverable until it meets strict pass criteria — plan, execute, score each criterion 1-10 with evidence, fix the lowest score first, repeat until all criteria score 8+. Built-in guards against score inflation and runaway loops (max 5 iterations, stop on 2 stalled rounds). Use when the user says 'loop until done', '될 때까지 반복', 'keep fixing until it passes', 'self-loop', or when reworking after a FAIL from $smoke-check, $gate-check, or $story-done."
---

# Self-Loop

Runs the plugin's self-iteration quality protocol on a single deliverable:
plan → execute → score → judge, repeated until every pass criterion scores
8/10 or higher. The full rule (including rationale) lives in
`../../rules/self-loop.md` — this skill is its executable form.

Writes: only the target deliverable locked in Phase 1 (e.g. `production/stories/<story>.md`, a GDD under `design/gdd/`, code under `src/`); the exit report goes to the conversation, not to a file.

Two traps this skill actively defends against:

1. **Score inflation** — the model grades itself leniently to exit the loop.
   Defense: criteria must be objectively verifiable, and any score of 8+
   must cite evidence (test output, command results, actual file content).
2. **Runaway loops** — criteria never reached, tokens burn forever.
   Defense: hard iteration cap (default 5) and a stall detector
   (2 consecutive rounds without the lowest score improving → stop and report).

---

## Phase 1: Lock the Target and Pass Criteria

1. **Target** — from the argument, state in one paragraph exactly what will
   be built or fixed. If no argument was given and no deliverable is obvious
   from context, ask the user for one and stop.

2. **Pass criteria** — 3 to 7 criteria, each one *objectively verifiable*:
   - ❌ "code quality is good"
   - ✅ "all tests pass (`<test command>` exits 0)"
   - ✅ "zero hardcoded gameplay values in changed files (grep evidence)"
   - ✅ "every acceptance criterion in the story file is demonstrably met"

   Sources, in priority order: `--criteria` argument → the governing artifact
   (story file, GDD section, PRD, gate report that failed) → propose 3-5
   yourself and show them before starting.

   If the deliverable mutates persistent state (money, orders, inventory,
   credits, messages), include the concurrency triad as a criterion:
   race conditions, partial writes, idempotency.

3. **Iteration cap** — `--max N` if given, otherwise 5.

Display the locked contract before looping:

```
Target: <one paragraph>
Criteria (all must score >= 8/10):
  C1. ...
  C2. ...
Max iterations: 5
```

---

## Phase 2: The Loop

Each iteration, in strict order:

1. **Plan** — name the ONE thing this iteration will do.
2. **Execute** — build or fix it. Actually run commands / write files;
   a plan is not an iteration.
3. **Score** — before grading anything, ask of each criterion:
   **"can a script decide this?"**
   - **Yes** → run the script. Its **exit code sets the score**, and your
     judgment does not override it. Non-zero → that criterion scores below 8,
     even if the work looks right to you. Record the command and the code:
     `pytest tests/ → exit 1 (3 failed)`. See
     [`../../docs/deterministic-gates.md`](../../docs/deterministic-gates.md) for the
     0/1/2/3 contract. A gate that could not run (exit 3) is NOT a pass —
     that criterion is unscored and the loop cannot declare DONE on it.
   - **No** (readability, tone, whether an argument holds) → grade 1-10, and:
     - cite evidence (test output, command result, file excerpt) — a score
       of 8+ **without quoted evidence is invalid**, re-score it lower;
     - name at least one remaining weakness, even at 9-10.

   Self-scoring is the fallback, not the default. Every criterion you grade by
   hand that a script could have measured is a criterion you are grading
   generously without knowing it.

   **A score below 8 is not yet a licence to rewrite.** Emit a defect ticket —
   `claim_id` / `defect_type` / `evidence` / `severity` — and fix only what the
   ticket names. Default `severity` is `local-fix`; `full-rewrite` is for
   structural defects only. **No ticket → preserve that part untouched.**
   Rule: [`../../rules/self-loop.md`](../../rules/self-loop.md) § 2.1.
4. **Judge** —
   - All criteria >= 8 **and** the policy axis clean → declare `DONE`, go to Phase 3.
   - `scripts/verify_policy.py → exit 2` → `BLOCKED`, whatever the scores say.
     Criteria met by breaking a rule is unsafe-success, not completion.
   - Cannot proceed for want of a permission, data, or a human decision →
     `BLOCKED`, not a failure. Say what would unblock it and where to resume.
   - Otherwise → declare `CONTINUE`, and the next iteration MUST target
     the lowest-scoring criterion first.

**Iteration input does not accumulate.** From iteration 2 on, re-inject only
four things: the previous output (or just the span being fixed), this round's
defect tickets, the violated criteria with their allowed values, and what must
be preserved. Re-feeding the whole context makes the model reinterpret the task
and undo earlier agreements. See `../../rules/self-loop.md` § 2.2.

Emit one progress line per iteration so the user can follow along:

```
[iter 2/5] lowest: C3 (5/10 — no error-path test) → this round: add error-path tests
```

**Hard rules:**
- Never claim the work is finished while any criterion is below 8.
- Do not ask the user questions mid-loop — judge and proceed autonomously.
  The only exits are DONE, the iteration cap, or the stall detector.
- If every criterion scores 9-10 on iteration 1, the criteria were too
  loose — tighten them once and re-score before declaring DONE.

**Stall detector:** if the lowest score fails to improve for 2 consecutive
iterations, STOP immediately. Do not attempt the same approach a third
time. Go to Phase 3 with result `STALLED`.

**Cap:** reaching `max` iterations without DONE → go to Phase 3 with
result `CAP REACHED`.

---

## Phase 3: Exit Report

Always produced — whether the loop finished, stalled, or hit the cap.
The user must be able to verify the result *without trusting the scores*.

```
## Self-Loop Report

Result: DONE | STALLED (<why>) | CAP REACHED
Iterations: N/5

| Criterion | Score | Evidence | Remaining risk |
|-----------|-------|----------|----------------|
| C1 ...    | 9/10  | test run: 42 passed | flaky on CI unverified |

Verify it yourself:
- <1-3 commands or file paths the user can check directly>

[If STALLED or CAP REACHED]
Blocked on: <root cause>
Tried: <approaches attempted>
Decision needed: <what the user must choose>
```

---

## Anti-patterns

- Starting the loop with no criteria — lock Phase 1 first.
- Scoring without fixing, or fixing without re-scoring — the 4 steps are a set.
- Polishing an already-high criterion while the lowest one waits.
- "One more try" after the stall detector or cap fires — stop means stop.
- Reporting only scores with no evidence and no way for the user to verify.
