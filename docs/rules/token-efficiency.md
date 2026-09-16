# Token Efficiency Rules

Eight lightweight rules to keep Codex agent collaboration efficient over long-running projects. Adopt as-is or fork.

---

## R1 — Commit messages: 5-15 lines

Structure:
```
<title — 1 line, imperative voice>

<core change — 3 bullets max, what changed and why>
<impact — 1-2 lines, what the user / team / build sees>
<next — 1 line, what comes after this commit>
```

Skip 50-line auto-generated bodies (HEREDOC dumps from agents). They cost reader time and rarely add value over a focused 5-15 line summary. If the change genuinely requires more explanation, write it in the PR description, not the commit body.

**Anti-pattern:** Commit messages that recap every file diff line-by-line, or that quote large portions of changed code.

---

## R2 — Meeting notes: ~80 lines for daily / per-topic preserves analysis

- **Daily roll-up** (`YYYY-MM-DD.md`) — keep ≤ 80 lines. Decisions, carryovers, links to commits — nothing more. Permanent insights become **separate memory files**, one-off observations live inline in commit messages.
- **Topic-specific** (`YYYY-MM-DD-<topic>.md`) — can be longer. **Preserve rejected-option analysis** including the reasoning that ruled them out — a future-you may revisit and need that context. Don't compress topic meetings into the daily roll-up.
- **Every meeting** has a header metadata table: date / facilitator / topic / decision status / cross-reference links.

---

## R3 — Bulk operations: skip mid-progress reports, verify once at the end

For changes spanning 5+ commits or 5+ files:
- **Don't** narrate each step ("now I'll do X", "now I'll do Y").
- **Do** run a single end-of-batch verification: build / test suite / smoke check / agent-only mid-progress (no user-facing report).

**Exception — keep mid-progress reports when:**
- Compile-risk territory (5+ new files in a tightly-typed language, plugin manifest changes that affect every session, hook config changes).
- Decision-authority territory (any choice the user owns — name / scope / spend / public-facing copy).

In those cases, surface a check-in even mid-batch. The cost of a 5-line "here's what I'm about to do" is much lower than the cost of an unwound batch.

---

## R4 — File reads: use parallel `Read` / `Grep` for independent inputs

When you need to read N files to make a decision, issue them as parallel tool calls in one message. This keeps the agent context warm and reduces wall-clock time. Sequential reads are only needed when each file's content informs which file to read next.

---

## R5 — Memory writes: permanent value only

Save to durable agent memory **only** when:
- The decision survives this session (rule, naming convention, tone filter, deferred-decision trigger).
- Future-you (or a different agent) needs to apply it without re-derivation.
- The information is not derivable from the codebase (i.e. not "this function does X" — that's just code).

Anything else lives in the commit message, the meeting note, or the inline `// ` comment near the affected code.

**Anti-pattern:** memory entries that summarise a single PR's changes. Use the PR description.

---

## R6 — User intent acknowledgments: 1-line, then act

When the user provides clear, executable intent ("OK", "go", "approve", "all of it", "reject"), respond with:
- **One short ack line** (`OK — proceeding`).
- **Immediately** start the action.

Don't:
- Re-summarize the user's message back at them.
- Re-list every step the user just approved.
- Ask follow-up clarifications when the original request was unambiguous.

This rule pairs with **R3** — many bulk operations begin with a single "OK" and just need to start running.

For paid API calls and other gated actions, this rule is **constrained by the gate** (e.g. `$api-cost-gate`) — the user's "OK" still needs to satisfy whatever pre-flight disclosure the gate requires.

---

## R7 — Reference docs: scope the read to the scenario, not "read everything every time"

When a task prompt points to a pile of reference material (a pricing sheet, a style guide, a brand doc), don't instruct the agent to read all of it on every run. Name which document applies to which scenario:

```
Only consult reference material for the scenario at hand.
Pricing questions: <pricing doc>
Wording/tone questions: <past announcement doc>
Logo/color questions: <brand doc>
For anything else, proceed without reading reference material.
```

Blanket "always read every doc" instructions inflate input size on every call regardless of whether that call needed the material, and a full-history fork reloads them per turn. Same principle as **R4** (parallel reads), applied to *whether* a read happens at all, not just how it's scheduled.

**Anti-pattern:** a standing instruction to re-read the full design doc / brand bible / API reference before every task, "just in case," when most tasks only touch one section of it.

---

## R8 — Delegated work: state completion criteria and decision boundaries upfront

Before handing off a multi-step task, give the agent three things in the same prompt instead of letting it stop to ask mid-task:

```
Done when: <concrete, checkable conditions>
Decide freely: <choices the agent can make on its own>
Confirm first: <irreversible or costly actions — sending, spending, deleting>
Everything else: assume the reasonable choice, keep going, and report
what you assumed at the end.
```

An agent that checks in on every ambiguous micro-decision burns a round-trip per question — each one reloads context on both sides. Most of those decisions don't need the user; they need permission to decide and a place to report the decision afterward. Reserve actual check-ins for the "confirm first" bucket.

**Anti-pattern:** a task handed off with no stated finish line, so the agent either stops after the first partial result to "check if this is right" or keeps going past where the user actually wanted it to stop.

---

## Adoption notes

- Adopt these rules in the project `AGENTS.md` so every Codex task inherits them.
- Customize the line counts (R1, R2) to your team's preference. The principle (lean over verbose) matters more than the exact thresholds.
- These rules are **pull-based** — they only fire when an agent is making a decision about how much to write / report. They don't replace standard linting, testing, or review.

---

## Origin

R1-R6 are distilled from real production logs of Claude Code sessions on a multi-month game project, listed in roughly the order each pattern surfaced. Each corrects a specific pattern that *cost reader time without delivering proportionate value*.

R7-R8 (2026-09-17) come from a different angle — a third-party summary of OpenAI's own Plus-plan quota guidance for ChatGPT Work/Codex, cross-checked against what this repo already had. See [docs/reasoning-effort.md](../reasoning-effort.md#2026-09-17-추가--astrasolterraluna-할당량-절약-팁-채택) for the source and what was deliberately left out.
