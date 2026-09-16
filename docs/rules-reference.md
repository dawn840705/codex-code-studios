# Workflow Rule References

These Markdown files are resources that Code Studios skills load explicitly.
They are **not** Codex command-approval rules and are not auto-enforced merely
because they live in `rules/`. Codex execpolicy uses `.codex/rules/*.rules`, a
different syntax and purpose. Do not copy these Markdown files there.

## Global Rules (always active, path-independent)

These apply to every project using the plugin, regardless of which files are being edited:

| Rule File | Enforces |
| ---- | ---- |
| `runtime-modes.md` | Which runtime is working this project, and therefore whether this plugin runs the **full studio** (`codex`), **stands down** (`claude`), or works a **partition** (`split`). Read from `production/runtime.txt`, never inferred from a `CLAUDE.md`/`.claude/` sighting — the same reason `track.txt` exists: the ambient signal is missing exactly when the question first matters. In `split` mode, write ownership is partitioned **by path** before work starts — `subagent-collaboration.md`'s lost-edit failure, one level up and worse, because the two runtimes share no session, context or tool log. Which strengths go where is **undecided** and the rule refuses to invent it |
| `verify-route.md` | Routes **verification** by reversibility, the axis `route-hint.md` does not cover: R1 (one edit undoes it) → the file's own gate · R2 (revert undoes it) → gates + review · R3 (needs coordination) → gates + a *separate* reviewing subagent + `$gate-check` · **R4 (irreversible, or costs users) → never unattended**. Uncertainty escalates; de-escalation must state a reason; the route is reported in the output |
| `self-loop.md` | Quality-gated deliverables are never one-shot: plan → execute → score (script exit code first, model grading only for the rest) → judge, until all criteria ≥ 8. Guards three failure modes: score inflation, runaway loops (max 5 iterations, stall detection), and **rewriting without evidence** (§ 2.1 — no defect ticket, no edit). Terminates DONE / FAILED / BLOCKED; the policy axis (`verify_policy.py`) can block regardless of scores. Executable form: `$self-loop` |
| `subagent-collaboration.md` | Multi-subagent parallel collaboration pattern for broad/deep design decisions — when to fan out, prompt requirements, result integration, meeting minutes. § 2.1: **write ownership is partitioned before spawning** — two agents never get the same file, because a lost Edit is the one failure mode that reports success |
| `decision-lifecycle.md` | Settled decisions do not reopen. A pinned decision needs three parts — the call, the evidence link, and the **revisit trigger** (a decision without one is deadlock, not closure); cap the pinned list at 20. Deprecated values are marked in the body, never deleted; product/ops calls live in `AGENTS.md`, technical ones in ADRs, never both. Agents report contrary evidence and stop rather than overturning a pin — a *decision-authority* axis, separate from `verify-route.md`'s reversibility axis, and never a reason to raise an R grade |
| `claim-confidence.md` | Verified facts, estimates, and unknowns are marked apart — source, `(추정)` + the arithmetic, or `[확인 필요]`. Statutes, prices, fees, competitor facts and API signatures are never written from memory. An unmarked estimate can fill a `self-loop.md` § 2.1 defect ticket (`defect_type: 누락`) if the evidence names *where you looked*. Not script-decidable, and not in `subagent-collaboration.md` § 3's mandatory prompt items — so it only catches when the caller puts it in the review prompt |
| `route-hint.md` | Pick a route before spawning: **light** (orchestrator handles it, 0 agents) / **standard** (1 specialist) / **heavy** (team fan-out + gates). Also emits a pre-task model recommendation: deterministic work uses a script/tool; judgment work keeps the session model. Savings come from fewer calls, not a cheaper model; splitting is the last resort. |
| `lesson-capture.md` | Every project doubles as teaching material. 5 standing triggers (repeated trap ×2, design hole exposed by feedback, assumption overturned, tooling pitfall, design pattern locked by data) prompt a lesson entry in `Documents/Lessons/`. A lesson proven wrong is **superseded, never deleted** (`supersedes:` front-matter + an INDEX marker) — the bad diagnosis is the only material that teaches the limits of a procedure. Executable form: `$lesson-log`, `$lesson-review` |
| `work-records.md` | What goes where when record types overlap (commit / session state / meeting minutes / lesson / ADR / report / CHANGELOG), and what the next session is required to read. § 2: a BLOCKED verdict needs somewhere to **accumulate** — `production/human-actions.md` holds the things only a person can do, split into execute (🔴) and decide (🟡), each with the reason it is a person's, completed items demoted rather than deleted. § 3: SessionStart stdout reaches the model on exit 0; PostToolUse stderr does not |

## Path-scoped review references

Files with `paths:` frontmatter describe where their guidance applies. The
relevant workflow skill or reviewing subagent must read the matching reference;
Codex does not automatically interpret the Markdown frontmatter as execpolicy.

| Rule File | Path Pattern | Enforces |
| ---- | ---- | ---- |
| `gameplay-code.md` | `src/gameplay/**` | Data-driven values, delta time, no UI references |
| `engine-code.md` | `src/core/**` | Zero allocs in hot paths, thread safety, API stability |
| `ai-code.md` | `src/ai/**` | Performance budgets, debuggability, data-driven params |
| `network-code.md` | `src/networking/**` | Server-authoritative, versioned messages, security |
| `ui-code.md` | `src/ui/**` | No game state ownership, localization-ready, accessibility |
| `frontend-code.md` | `src/app/**`, `src/components/**`, `src/pages/**`, `app/**`, `components/**` | **Product track.** Server/client state separation, i18n from day one, keyboard operability, four render states, no layout shift, nothing secret in the bundle |
| `api-code.md` | `src/api/**`, `src/server/**`, `src/routes/**`, `api/**` | **Product track.** Boundary validation, per-resource authorization, additive versioning, idempotent mutations, no PII in logs, migrations only |
| `design-docs.md` | `design/gdd/**` | Required 8 sections, formula format, edge cases |
| `narrative.md` | `design/narrative/**` | Lore consistency, character voice, canon levels |
| `data-files.md` | `assets/data/**` | JSON validity, naming conventions, schema rules |
| `test-standards.md` | `tests/**` | Test naming, coverage requirements, fixture patterns |
| `prototype-code.md` | `prototypes/**` | Relaxed standards, README required, hypothesis documented |
| `shader-code.md` | `assets/shaders/**` | Naming conventions, performance targets, cross-platform rules |
