# Route Hint — Call-Count Routing

**Global rule. Applies to every project and every domain.**

`$studio-orchestrator` says *"don't spawn agents just because they exist — if
the task is simple, handle it directly."* This rule turns that instinct into a
repeatable routing decision.

Upstream measurement puts a number on what that feel costs. Rewriting a
10,000-character text as 7 chunks burned **610K tokens**. The same text in a
single call: **134K, at equal quality.** A 4.5× difference, and the cause was
not model choice — it was **reloading the rulebook and the diagnosis into every
chunk.**

A studio with 45 agents, each reloading its own context, has exactly that
structure.

## Two principles

**Savings come from fewer calls, not from a cheaper model.** Never silently
downgrade the model or reasoning effort to save money — those choices belong
to the user. Cut the number of calls instead: several small calls each reload
the same context.

An explicit user authorization for automatic **effort-only** selection is a
separate axis: follow [`reasoning-effort.md`](reasoning-effort.md). Observation
alone grants no runtime authority. Keep the model fixed, preserve user overrides,
and never reduce required verification or change approval policy with effort.

**Splitting is the last resort.** Prefer one call. Split only when a hard limit
forces it, and when you do, make sure the shared context is loaded once — not
once per piece.

## The three routes

Pick a route before spawning anything.

| Route | Signals | Action |
|---|---|---|
| **light** | 1-2 files, single domain, repeating an existing pattern | Orchestrator handles it directly. **Zero agents spawned.** |
| **standard** | Single domain, but a genuine design judgment is needed | One specialist agent |
| **heavy** | Multiple domains, or a hard-to-reverse change, or evidence is explicitly required | Team fan-out + gates |

When torn between two routes, take the lighter one. Escalating costs one more
call; over-fanning-out costs N.

## Escalate on signals, not on nerves

Move up a route when a concrete signal says so:

- The work touches a boundary you cannot see the far side of
- The change is hard to undo (migrations, deletions, published output)
- The user asked for evidence, review, or a second opinion
- A gate already failed and you are reworking (see
  [`self-loop.md`](self-loop.md))

Do **not** escalate because the task merely sounds important, or to look
thorough. Fan-out that produces four summaries of the same file is not
diligence — it is the 4.5× above.

## Model axis — standing policy only

Call count is the first axis; model tier is the second. The no-silent-downgrade
principle above stands: **the orchestrator never picks a cheaper model on its
own judgment.** What unlocks tier routing is a **standing policy the user has
set** — a line in the project's `AGENTS.md` naming which lanes run on which
tier. With that line in place, routing is obedience, not initiative.

The recommended standing policy (adopt by copying into project `AGENTS.md`):

| Lane | Tier | Why |
|---|---|---|
| Mechanical sweeps — exhaustive search/inventory, format checks, link/path audits, file listing | lower reasoning effort if the user has pre-authorized it | The output is an enumeration; judgment adds nothing |
| Exploration/scouting with a defined question | mid tier or session model | Misreading the codebase here poisons every later step |
| Design judgment, code review, anything adjacent to a user decision | **session model, never downgraded** | This is what the user is paying the premium tier for |
| Deterministic transforms (renames, link rewrites, bulk edits) | **no model at all — a script** | Exit code beats token spend; see `doc_relink.py` |

Two guards:

- When unsure which lane a task is in, it is not a mechanical sweep. Inherit
  the session model.
- A downgraded agent that starts making judgment calls (proposing designs,
  resolving ambiguity) is a routing error — pull the work back up, don't let
  the cheap lane's answer stand.

Pick the lane **before** dispatching, not mid-task: a lower tier or lower
reasoning effort doesn't refund the quota already spent on a higher one, and a
lower tier is not automatically worse — a low-effort pass on a stronger model
can outperform a high-effort pass on a weaker one, so "start low, escalate on
a concrete signal" beats "start high to be safe." Source:
[docs/reasoning-effort.md](../docs/reasoning-effort.md#2026-09-17-추가--astrasolterraluna-할당량-절약-팁-채택).

## Reference implementation

`scripts/prepare_monolith_input.py` routes Korean rewriting deterministically:

```python
ROUTE_HEAVY_MIN_CHARS = 15000   # over this  → heavy
ROUTE_HEAVY_MIN_TELLS = 8       # risk=high AND tells >= 8 → heavy
ROUTE_LIGHT_MAX_TELLS = 2       # tells <= 2 AND risk in (low, medium) → light
# otherwise → standard
```

Note what it leaves out. Z-scores and density metrics are **deliberately
excluded** because the 70 baseline cells backing them are placeholders. An
unvalidated signal is kept out of the decision entirely rather than used with a
caveat. Copy that discipline: if you cannot trust a signal, do not let it pick
the route.

## What this rule does not decide

Everything above routes **production** — how many agents make the thing. It says
nothing about how hard the result gets **checked**, and those are independent
axes: a one-line edit to a published config is the lightest production route and
the heaviest verification route.

Route the checking separately with [`verify-route.md`](verify-route.md), by
reversibility (R1-R4). Do not infer one from the other.

## Related

- [`verify-route.md`](verify-route.md) — routes verification; this file routes
  production. Decide both, independently
- [`self-loop.md`](self-loop.md) — iterate until criteria pass; route-hint
  decides how much machinery each iteration gets
- [`docs/deterministic-gates.md`](../docs/deterministic-gates.md) — heavy-route
  gates judge by exit code, not by self-assessment
- [`subagent-collaboration.md`](subagent-collaboration.md) — how to fan out
  once you have decided on heavy
