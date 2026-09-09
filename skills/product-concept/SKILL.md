---
name: product-concept
description: "Guided authoring of the product-level concept document for an app/web/service project — problem statement, target users, value proposition, differentiation, and scope tiers — written to product/prd/product-concept.md. This is the document every feature PRD is derived from, so run it before $create-prd. Use when starting a product-track project, when $create-prd or $gate-check reports the product concept is missing, or when the user says 'define the product', 'what are we building', 'write the product concept'. Do NOT use for a game concept (that is $brainstorm → design/gdd/game-concept.md), and do NOT use for a single feature's requirements (that is $create-prd)."
---

When this skill is invoked:

## 1. Parse Arguments & Check Track

Resolve the review mode (once, store for all gate spawns this run):

1. If `--review [full|lean|solo]` was passed → use that
2. Else read `production/review-mode.txt` → use that value
3. Else → default to `lean`

**Confirm the track before writing anything.** This skill produces a *product*
concept. If `PROJECT_TYPE` is `game`, stop and route to `$brainstorm` instead —
the two documents are not interchangeable and `design/gdd/game-concept.md` is
what the game track's gates look for. If `PROJECT_TYPE` is `unknown`, ask once,
write the answer to `production/track.txt`, and continue.

If `product/prd/product-concept.md` already exists, do **not** overwrite. Read
it, identify missing or placeholder sections, and fill only those.
Never touch section content that is already written.

---

## 2. Gather Context (Read Phase)

Read before asking the user anything:

- **Stack pin**: `.codex/studio/technical-preferences.md` — platform and framework
  constrain what the product can be. If missing, note it; the concept can be
  written first, but say so rather than assuming a stack.
- **Existing PRDs**: Glob `product/prd/prd-*.md`. On a project that grew feature
  PRDs before anyone wrote the concept, those PRDs are the evidence of what the
  product actually became. Read them and reconcile — do not invent a concept that
  contradicts shipped features.
- **Prior exploration**: any `$brainstorm` output or discovery notes the user
  points at.

---

## 3. Author Section by Section (Write Phase)

Draft every section from what you read. Three choices are K1 — taste and strategy
decide them, not evidence: **target segment, scope tier boundaries, monetization
posture**. Present each as a decision item (recommendation, alternatives, why) and
let the user choose; do not guess them, because a wrong assumption here propagates
into every downstream PRD. Every other section: draft it, mark assumptions per
`../../rules/claim-confidence.md`, and continue.

**Required sections:**

1. **One-line definition** — what this is, in a sentence a stranger understands.
2. **Problem & opportunity** — whose problem, how they solve it today, why that
   is bad enough to change. **A problem statement with no current alternative is
   a warning sign**, not a green field: it usually means the problem is not felt.
3. **Target users** — primary segment first, with the situation they are in when
   they would reach for this. Secondary segments are explicitly secondary.
4. **Value proposition & differentiation** — what this does that the existing
   options do not. Name the alternatives, including "do nothing manually in a
   spreadsheet", which is the most common competitor and the most often ignored.
5. **Core loop** — the repeating user action that makes the product work. If the
   product has no repeat use, say so explicitly and state what replaces retention.
6. **Scope tiers** — MVP / next / later. The MVP tier is what you would ship if
   you had to ship in a third of the planned time.
7. **Success metrics** — how you will know it worked, and the threshold that
   would make you stop. Apply `../../rules/claim-confidence.md` § 3.1: at launch
   sample sizes, name raw counts, not ratios.
8. **Risks & assumptions** — the assumptions that, if wrong, invalidate the
   concept. Mark each as verified, estimated, or unverified per
   `../../rules/claim-confidence.md`.
9. **Out of scope** — what this product is deliberately not. A concept with no
   out-of-scope section has not made any decisions yet.

Any market size, competitor fact, pricing, or regulatory claim follows
`../../rules/claim-confidence.md`: cite the source, or mark `(추정)` with the
arithmetic, or `[확인 필요]`. Do not write these from memory. Mark `[확인 필요]`
and continue; list them in the report.

---

## 4. Director Gate

See `../../docs/director-gates.md` for the full check pattern.

- `full` → spawn `product-manager` as a Codex subagent to review the concept for internal
  consistency (does the core loop serve the stated problem, do the scope tiers
  hold the value proposition) before writing.
- `lean` / `solo` → skip. Note the skip in the output.

---

## 5. Write

Write `product/prd/product-concept.md`, creating the directory if needed. A K1
choice still open stays in the file as `[BLOCKED: user decision — <choice>]`; write
the rest. Report the path, the revert command (`git checkout -- <path>`), and the
open choices.

---

## 6. Report the Verdict

After writing, state one of these — the downstream skills and `$gate-check
architecture` depend on knowing which:

- **COMPLETE** — all nine sections written, every claim either sourced or marked,
  no `[확인 필요]` blocking an MVP-tier decision. `$create-prd` can start.
- **CONCERNS** — written and usable, but list each `[확인 필요]` that a feature PRD
  will inherit. These are the assumptions that will propagate; name them here or
  they will surface as facts in three PRDs' time.
- **BLOCKED** — a K1 decision is missing (target segment, monetization posture,
  a regulatory question). Do not guess it to finish the document. Record it in
  `production/human-actions.md` per `../../rules/work-records.md` § 2 and name
  what resumes the run.

---

## 7. Next Steps

List these in order:

1. "Pin the stack in `.codex/studio/technical-preferences.md` if it is not pinned yet — the product-track equivalent of `$setup-engine`"
2. "Write the first feature PRD with `$create-prd <feature>` — one per MVP-tier feature"
3. "Design the screens with `$ux-design` once the MVP features have PRDs"
4. "Validate readiness to advance with `$gate-check architecture`"

---

## Relationship to Neighbouring Skills

| Skill | Layer | Artifact |
|---|---|---|
| `$brainstorm` | exploration, **game** framing | `design/gdd/game-concept.md` |
| **`$product-concept`** | **product level** | `product/prd/product-concept.md` |
| `$create-prd` | **feature level** | `product/prd/prd-<feature>.md` |

`$create-prd` reads this document and fails without it. That was the gap this
skill closes: the product track required the artifact and named no skill that
wrote it.
