---
name: gate-check
description: "Validate readiness to advance between development phases, on either track. Produces a PASS/CONCERNS/FAIL verdict with specific blockers and required artifacts. Use when user says 'are we ready to move to X', 'can we advance to production', 'check if we can start the next phase', 'pass the gate'."
---

# Phase Gate Validation

This skill validates whether the project is ready to advance to the next development
phase. It checks for required artifacts, quality standards, and blockers.

**Distinct from `$project-stage-detect`**: That skill is diagnostic ("where are we?").
This skill is prescriptive ("are we ready to advance?" with a formal verdict).

## Stages — two tracks

**Resolve the track first.** The `detect-project-type.sh` hook prints
`PROJECT_TYPE`. `game` → game track. `web`/`mobile`/`service` → product track.
`unknown` → ask once, write `production/track.txt`, then run. Phase names are **not
interchangeable between tracks**, and the two tracks are not 1:1 — product
`discovery` covers game `concept` + `systems-design`, and product `build` covers
`pre-production` + `production`. Never translate a phase name by position.

**Game track (7):**

1. **Concept** — Brainstorming, game concept document
2. **Systems Design** — Mapping systems, writing GDDs
3. **Technical Setup** — Engine config, architecture decisions
4. **Pre-Production** — Prototyping, vertical slice validation
5. **Production** — Feature development (Epic/Feature/Task tracking active)
6. **Polish** — Performance, playtesting, bug fixing
7. **Release** — Launch prep, certification

**Product track (6):**

1. **Discovery** — Product concept, feature PRDs, UX specs
2. **Architecture** — Stack pinned, ADRs, accessibility tier
3. **Build** — Epics, stories, sprints, implementation
4. **Hardening** — QA, regression, security, performance
5. **Ship** — Release and launch checklists
6. **Growth** — Metrics, milestone reviews, feature viability

`live-ops` is **not a gate target** on either track — it is `post_release` in
`agent-packs.yaml`, entered by human judgement, and `check_phase.py` never
returns it.

**When a gate passes**, write the new stage name to `production/stage.txt`
(single line, e.g. `Production` or `Hardening`) and the report to
`production/gate-checks/gate-check-[target-phase].md`. Both are R-grade writes:
report the paths and the revert command.

---

## 1. Parse Arguments

**Track first.** Read `PROJECT_TYPE` from the session-start hook output, or run
`../../hooks/detect-project-type.sh`. `game` → game gates. `web`/`mobile`/
`service` → product gates. `unknown` → ask once which the project is, write
`production/track.txt`, then continue (K1). Do not guess from the directory
layout — a product project that happens to have a `design/` folder would be
misrouted into the game gates.

If the target phase names a phase from the **other** track (e.g. `$gate-check
polish` on a service project), do not translate it. Say which track the project
is on, list that track's gate targets, and stop — the argument is not on this
track (K2).

**Target phase:** `the first invocation argument` (blank = auto-detect current stage, then validate next transition)

Also resolve the review mode (once, store for all gate spawns this run):
1. If `--review [full|lean|solo]` was passed → use that
2. Else read `production/review-mode.txt` → use that value
3. Else → default to `lean`

Note: in `solo` mode, director spawns (CD-PHASE-GATE, TD-PHASE-GATE, PR-PHASE-GATE, AD-PHASE-GATE) are skipped — gate-check becomes artifact-existence checks only. In `lean` mode the four PHASE-GATEs run as a **self-review** (no spawn): work through each gate prompt as a checklist and cite the `check_phase.py` / `verify_policy.py` exit codes. In `full` mode spawn them as separate reviewing subagents.

- **With argument**: `$gate-check production` — validate readiness for that specific phase
- **No argument**: auto-detect the current stage with `scripts/check_phase.py`
  (the source `$project-stage-detect` reads) and run the gate for
  [Current] → [Next]. Take the detected stage unless `production/stage.txt` names
  a later one; if you deviate, name the reason in the report. Put "Detected
  stage: **[stage]** (check_phase.py → exit N)" on the report's first line. No
  confirmation question.

---

## 2. Phase Gate Definitions

**Use only the gates for the resolved track.** Running a game gate on a product
project produces a FAIL made entirely of artifacts that project was never
supposed to have.

---

# Game Track Gates

### Gate: Concept → Systems Design

**Required Artifacts:**
- [ ] `design/gdd/game-concept.md` exists and has content
- [ ] Game pillars defined (in concept doc or `design/gdd/game-pillars.md`)
- [ ] Visual Identity Anchor section exists in `design/gdd/game-concept.md` (from brainstorm Phase 4 art-director output)

**Quality Checks:**
- [ ] Game concept has been reviewed (`$design-review` verdict not MAJOR REVISION NEEDED)
- [ ] Core loop is described and understood
- [ ] Target audience is identified
- [ ] Visual Identity Anchor contains a one-line visual rule and at least 2 supporting visual principles

---

### Gate: Systems Design → Technical Setup

**Required Artifacts:**
- [ ] Systems index exists at `design/gdd/systems-index.md` with at least MVP systems enumerated
- [ ] All MVP-tier GDDs exist in `design/gdd/` and individually pass `$design-review`
- [ ] A cross-GDD review report exists in `design/gdd/` (from `$review-all-gdds`)

**Quality Checks:**
- [ ] All MVP GDDs pass individual design review (8 required sections, no MAJOR REVISION NEEDED verdict)
- [ ] `$review-all-gdds` verdict is not FAIL (cross-GDD consistency and design theory checks pass)
- [ ] All cross-GDD consistency issues flagged by `$review-all-gdds` are resolved or explicitly accepted
- [ ] System dependencies are mapped in the systems index and are bidirectionally consistent
- [ ] MVP priority tier is defined
- [ ] No stale GDD references flagged (older GDDs updated to reflect decisions made in later GDDs)

---

### Gate: Technical Setup → Pre-Production

**Required Artifacts:**
- [ ] Engine chosen (AGENTS.md Technology Stack is not `[CHOOSE]`)
- [ ] Technical preferences configured (`.codex/studio/technical-preferences.md` populated)
- [ ] Art bible exists at `design/art/art-bible.md` with at least Sections 1–4 (Visual Identity Foundation)
- [ ] At least 3 Architecture Decision Records in `docs/architecture/` covering
      Foundation-layer systems (scene management, event architecture, save/load)
- [ ] Engine reference docs exist in `docs/engine-reference/[engine]/`
- [ ] Test framework initialized: `tests/unit/` and `tests/integration/` directories exist
- [ ] CI/CD test workflow exists at `.github/workflows/tests.yml` (or equivalent)
- [ ] At least one example test file exists to confirm the framework is functional
- [ ] Master architecture document exists at `docs/architecture/architecture.md`
- [ ] Architecture traceability index exists at `docs/architecture/architecture-traceability.md`
- [ ] `$architecture-review` has been run (a review report file exists in `docs/architecture/`)
- [ ] `design/accessibility-requirements.md` exists with accessibility tier committed
- [ ] `design/ux/interaction-patterns.md` exists (pattern library initialized, even if minimal)

**Quality Checks:**
- [ ] Architecture decisions cover core systems (rendering, input, state management)
- [ ] Technical preferences have naming conventions and performance budgets set
- [ ] Accessibility tier is defined and documented (even "Basic" is acceptable — undefined is not)
- [ ] At least one screen's UX spec started (often the main menu or core HUD is designed during Technical Setup)
- [ ] All ADRs have an **Engine Compatibility section** with engine version stamped
- [ ] All ADRs have a **GDD Requirements Addressed section** with explicit GDD linkage
- [ ] No ADR references APIs listed in `docs/engine-reference/[engine]/deprecated-apis.md`
- [ ] All HIGH RISK engine domains (per VERSION.md) have been explicitly addressed
      in the architecture document or flagged as open questions
- [ ] Architecture traceability matrix has **zero Foundation layer gaps**
      (all Foundation requirements must have ADR coverage before Pre-Production)

**ADR Circular Dependency Check**: For all ADRs in `docs/architecture/`, read each ADR's
"ADR Dependencies" / "Depends On" section. Build a dependency graph (ADR-A → ADR-B means
A depends on B). If any cycle is detected (e.g. A→B→A, or A→B→C→A):
- Flag as **FAIL**: "Circular ADR dependency: [ADR-X] → [ADR-Y] → [ADR-X].
  Neither can reach Accepted while the cycle exists. Remove one 'Depends On' edge to
  break the cycle."

**Engine Validation** (read `docs/engine-reference/[engine]/VERSION.md` first):
- [ ] ADRs that touch post-cutoff engine APIs are flagged with Knowledge Risk: HIGH/MEDIUM
- [ ] `$architecture-review` engine audit shows no deprecated API usage
- [ ] All ADRs agree on the same engine version (no stale version references)

---

### Gate: Pre-Production → Production

**Required Artifacts:**
- [ ] At least 1 prototype in `prototypes/` with a README
- [ ] First sprint plan exists in `production/sprints/`
- [ ] Art bible is complete (all 9 sections) and AD-ART-BIBLE sign-off verdict is recorded in `design/art/art-bible.md`
- [ ] Character visual profiles exist for key characters referenced in narrative docs
- [ ] All MVP-tier GDDs from systems index are complete
- [ ] Master architecture document exists at `docs/architecture/architecture.md`
- [ ] At least 3 ADRs covering Foundation-layer decisions exist in `docs/architecture/`
- [ ] Control manifest exists at `docs/architecture/control-manifest.md`
      (generated by `$create-control-manifest` from Accepted ADRs)
- [ ] Epics defined in `production/epics/` with at least Foundation and Core
      layer epics present (use `$create-epics layer: foundation` and
      `$create-epics layer: core` to create them, then `$create-stories [epic-slug]`
      for each epic)
- [ ] Vertical Slice build exists and is playable (not just scope-defined)
- [ ] Vertical Slice has been playtested with at least 3 sessions (internal OK)
- [ ] Vertical Slice playtest report exists at `production/playtests/` or equivalent
- [ ] UX specs exist for key screens: main menu, core gameplay HUD (at `design/ux/`), pause menu
- [ ] HUD design document exists at `design/ux/hud.md` (if game has in-game HUD)
- [ ] All key screen UX specs have passed `$ux-review` (verdict APPROVED or NEEDS REVISION accepted)

**Quality Checks:**
- [ ] **Core loop fun is validated** — playtest data confirms the central mechanic is enjoyable, not just functional. Explicitly check the Vertical Slice playtest report.
- [ ] UX specs cover all UI Requirements sections from MVP-tier GDDs
- [ ] Interaction pattern library documents patterns used in key screens
- [ ] Accessibility tier from `design/accessibility-requirements.md` is addressed in all key screen UX specs
- [ ] Sprint plan references real story file paths from `production/epics/`
      (not just GDDs — stories must embed GDD req ID + ADR reference)
- [ ] **Vertical Slice is COMPLETE**, not just scoped — the build demonstrates the full core loop end-to-end. At least one complete [start → challenge → resolution] cycle works.
- [ ] Architecture document has no unresolved open questions in Foundation or Core layers
- [ ] All ADRs have Engine Compatibility sections stamped with the engine version
- [ ] All ADRs have ADR Dependencies sections (even if all fields are "None")
- [ ] Manual validation confirms GDDs + architecture + epics are coherent
      (run `$review-all-gdds` and `$architecture-review` if not done recently)
- [ ] **Core fantasy is delivered** — at least one playtester independently described an experience that matches the Player Fantasy section of the core system GDDs (without being prompted).

**Vertical Slice Validation** (FAIL if any item is NO):
- [ ] A human has played through the core loop without developer guidance
- [ ] The game communicates what to do within the first 2 minutes of play
- [ ] No critical "fun blocker" bugs exist in the Vertical Slice build
- [ ] The core mechanic feels good to interact with (subjective — K3, goes into the Section 4 block)

> **Note**: If any Vertical Slice Validation item is FAIL, the verdict is automatically FAIL
> regardless of other checks. Advancing without a validated Vertical Slice is the #1 cause of
> production failure in game development (per GDC postmortem data from 155 projects).

---

### Gate: Production → Polish

**Required Artifacts:**
- [ ] `src/` has active code organized into subsystems
- [ ] All core mechanics from GDD are implemented (cross-reference `design/gdd/` with `src/`)
- [ ] Main gameplay path is playable end-to-end
- [ ] Test files exist in `tests/unit/` and `tests/integration/` covering Logic and Integration stories
- [ ] All Logic stories from this sprint have corresponding unit test files in `tests/unit/`
- [ ] Smoke check has been run with a PASS or PASS WITH WARNINGS verdict — report exists in `production/qa/`
- [ ] QA plan exists in `production/qa/` (generated by `$qa-plan`) covering this sprint or final production sprint
- [ ] QA sign-off report exists in `production/qa/` (generated by `$team-qa`) with verdict APPROVED or APPROVED WITH CONDITIONS
- [ ] At least 3 distinct playtest sessions documented in `production/playtests/`
- [ ] Playtest reports cover: new player experience, mid-game systems, and difficulty curve
- [ ] Fun hypothesis from Game Concept has been explicitly validated or revised

**Quality Checks:**
- [ ] Tests are passing (run test suite via Bash)
- [ ] No critical/blocker bugs in any bug tracker or known issues
- [ ] Core loop plays as designed (compare to GDD acceptance criteria)
- [ ] Performance is within budget (check technical-preferences.md targets)
- [ ] Playtest findings have been reviewed and critical fun issues addressed (not just documented)
- [ ] No "confusion loops" identified — no point in the game where >50% of playtesters got stuck without knowing why
- [ ] Difficulty curve matches the Difficulty Curve design doc (if one exists at `design/difficulty-curve.md`)
- [ ] All implemented screens have corresponding UX specs (no "designed in-code" screens)
- [ ] Interaction pattern library is up-to-date with all patterns used in implementation
- [ ] Accessibility compliance verified against committed tier in `design/accessibility-requirements.md`

---

### Gate: Polish → Release

**Required Artifacts:**
- [ ] All features from milestone plan are implemented
- [ ] Content is complete (all levels, assets, dialogue referenced in design docs exist)
- [ ] Localization strings are externalized (no hardcoded player-facing text in `src/`)
- [ ] QA test plan exists (`$qa-plan` output in `production/qa/`)
- [ ] QA sign-off report exists (`$team-qa` output — APPROVED or APPROVED WITH CONDITIONS)
- [ ] All Must Have story test evidence is present (Logic/Integration: test files pass; Visual/Feel/UI: sign-off docs in `production/qa/evidence/`)
- [ ] Smoke check passes cleanly (PASS verdict) on the release candidate build
- [ ] No test regressions from previous sprint (test suite passes fully)
- [ ] Balance data has been reviewed (`$balance-check` run)
- [ ] Release checklist completed (`$release-checklist` or `$launch-checklist` run)
- [ ] Store metadata prepared (if applicable)
- [ ] Changelog / patch notes drafted

**Quality Checks:**
- [ ] Full QA pass signed off by `qa-lead`
- [ ] All tests passing
- [ ] Performance targets met across all target platforms
- [ ] No known critical, high, or medium-severity bugs
- [ ] Accessibility basics covered (remapping, text scaling if applicable)
- [ ] Localization verified for all target languages
- [ ] Legal requirements met (EULA, privacy policy, age ratings if applicable)
- [ ] Build compiles and packages cleanly

---

# Product Track Gates

These are leaner than the game gates on purpose. The game track accumulated its
checks over several releases of real use; these encode what the catalog requires
plus the judgements a script cannot make. **Add to them from observed failures,
not from symmetry with the game track.**

### Gate: Discovery → Architecture

**Required Artifacts:**
- [ ] `product/prd/product-concept.md` exists with real content (from `$product-concept`)
- [ ] `.codex/studio/technical-preferences.md` is populated — stack and versions pinned, not `[CHOOSE]`
- [ ] At least one feature PRD in `product/prd/prd-*.md` (from `$create-prd`)
- [ ] UX specs exist in `design/ux/` for the primary flow

**Quality Checks:**
- [ ] The product concept names the alternatives users have today — including doing it manually. A concept with no named alternative has not been tested against reality
- [ ] MVP scope tier is defined and is genuinely smaller than the full vision
- [ ] Out-of-scope section exists and is non-empty
- [ ] Every MVP-tier feature in the concept either has a PRD or is explicitly deferred — no silent gaps
- [ ] PRDs do not contradict each other or the concept (`$design-review <prd>` verdict is not MAJOR REVISION NEEDED — that is the catalog's `prd-review` step)
- [ ] Success metrics name a threshold that would make you stop, not only ones that would make you continue
- [ ] Market, pricing, and competitor claims are sourced or marked per `../../rules/claim-confidence.md`

---

### Gate: Architecture → Build

**Required Artifacts:**
- [ ] Master architecture document exists at `docs/architecture/architecture.md`
- [ ] At least 3 ADRs in `docs/architecture/` covering foundation decisions (data model, auth, state management, deployment)
- [ ] `$architecture-review` has been run (a review report exists in `docs/architecture/`)
- [ ] `design/accessibility-requirements.md` exists with the tier committed
- [ ] Test framework initialized (`tests/` with at least one running example) and a CI workflow exists

**Quality Checks:**
- [ ] Every ADR links the PRD requirement it serves — an ADR with no requirement is a preference
- [ ] No circular ADR dependencies (build the graph from each ADR's "Depends On"; a cycle is a **FAIL** — neither ADR can reach Accepted)
- [ ] Accessibility tier is defined (even "Basic"; undefined is not acceptable)
- [ ] Data retention, PII handling, and third-party processors are addressed if the product stores user data — not deferred to Hardening, where changing them means a migration
- [ ] Per-user cost of any paid API is estimated with the arithmetic shown, and a cap exists (`$api-cost-gate`)

---

### Gate: Build → Hardening

**Required Artifacts:**
- [ ] Epics in `production/epics/` and stories in `production/stories/`
- [ ] At least one completed sprint in `production/sprints/`
- [ ] All Must Have stories are marked done (`$story-done` verdicts recorded)
- [ ] Test evidence present for Must Have stories (test files pass; UI/visual items have sign-off in `production/qa/evidence/`)

**Quality Checks:**
- [ ] The MVP feature set from the product concept is implemented — not a different set that emerged along the way. If it diverged, the concept is updated to say so
- [ ] `$smoke-check` passes on the current build
- [ ] No test regressions from the previous sprint
- [ ] Analytics events for the success metrics are actually instrumented — a metric with no event is a plan, not a measurement
- [ ] Error and empty states exist for the primary flow (the states QA finds last and users hit first)

---

### Gate: Hardening → Ship

**Required Artifacts:**
- [ ] QA test plan exists (`$qa-plan` output in `production/qa/`)
- [ ] QA sign-off recorded (`$team-qa` — APPROVED or APPROVED WITH CONDITIONS)
- [ ] `$security-audit` has been run and its findings are resolved or explicitly accepted
- [ ] `$perf-profile` results recorded against a stated budget
- [ ] Regression suite exists and passes (`$regression-suite`)

**Quality Checks:**
- [ ] No known critical or high-severity bugs open
- [ ] Performance budget met on the **lowest** target device or connection, not the development machine
- [ ] Legal surface covered where applicable: privacy policy, terms, data-deletion path, age rating, cookie/consent
- [ ] Store or platform policy checklist passed if shipping to an app store
- [ ] Rollback path is written down and has been tried at least once — an untried rollback is an assumption

---

### Gate: Ship → Growth

**Required Artifacts:**
- [ ] `$release-checklist` and `$launch-checklist` completed
- [ ] Release notes or changelog published
- [ ] Store listing / landing copy finalized if applicable
- [ ] Monitoring in place: error reporting, uptime, and cost alerts

**Quality Checks:**
- [ ] Someone is named as responsible for the first-week response, and the escalation path exists
- [ ] Support intake exists — an address, form, or channel a user can actually reach
- [ ] Success metric baselines are captured **before** launch traffic arrives. After is too late; there is nothing to compare against
- [ ] Cost per active user is estimated with a cap or an alert threshold set

---

## 3. Run the Gate Check

**Before running artifact checks**, read `docs/consistency-failures.md` if it exists.
Extract entries whose Domain matches the target phase (e.g., if checking
Systems Design → Technical Setup, pull entries in Economy, Combat, or any GDD domain;
if checking Technical Setup → Pre-Production, pull entries in Architecture, Engine).
Carry these as context — recurring conflict patterns in the target domain warrant
increased scrutiny on those specific checks.

For each item in the target gate:

### Artifact Checks
- Use `Glob` and `Read` to verify files exist and have meaningful content
- Don't just check existence — verify the file has real content (not just a template header)
- For code checks, verify directory structure and file counts

**Game track only** — this gate exists on the game track, so a product project never
reaches it. Everything else in section 3 runs on both tracks; where it names a game
path, read the product equivalent (`design/gdd/` → `product/prd/`, GDD → PRD).

**Systems Design → Technical Setup gate — cross-GDD review check**:
Use `Glob('design/gdd/gdd-cross-review-*.md')` to find the `$review-all-gdds` report.
If no file matches, mark the "cross-GDD review report exists" artifact as **FAIL** and
surface it prominently: "No `$review-all-gdds` report found in `design/gdd/`. Run
`$review-all-gdds` before advancing to Technical Setup."
If a file is found, read it and check the verdict line: a FAIL verdict means the
cross-GDD consistency check failed and must be resolved before advancing.

### Quality Checks
- For test checks: Run the test suite via `Bash` if a test runner is configured
- For design review checks: game — `Read` the GDD and check for the 8 required sections;
  product — `Read` the PRD in `product/prd/` and check its template sections, with every
  success metric measurable and every acceptance criterion testable
- For performance checks: `Read` technical-preferences.md and compare against any
  profiling data in `tests/performance/` or recent `$perf-profile` output
- For localization checks: `Grep` for hardcoded strings in `src/`

### Cross-Reference Checks
- Compare the requirement documents against `src/` implementations — `design/gdd/` on the
  game track, `product/prd/` on the product track
- Check that every system referenced in architecture docs has corresponding code
- Verify sprint plans reference real work items

---

## 4. Collaborative Assessment (K3 — asked once)

Items only a person can observe (core loop feel, informal playtests, profiling
that is not on disk) are **MANUAL CHECK NEEDED**. Collect them; finish sections
3, 4b and 5a first; then ask them all in **one question block** beneath the
verdict, e.g. "Has the core loop been playtested?", "Has informal testing been
done?", "Is profiling data available?".

**Never assume PASS for unverifiable items.** An unanswered item stays MANUAL
CHECK NEEDED, is appended to `production/human-actions.md`, and caps the verdict
at CONCERNS.

---

## 4b. Director Panel Assessment

Before generating the final verdict, run the four PHASE-GATEs according to the resolved review mode (`../../docs/director-gates.md`):

- `lean` (default) — **self-review, no spawn.** Work through the four gate prompts as one checklist, run `check_phase.py` and `verify_policy.py`, and record `[GATE-ID] self-review — Lean mode · check_phase.py exit N · verify_policy.py exit N` for each.
- `full` — spawn all four directors as **parallel subagents** using the parallel gate protocol. Issue all four Codex subagent calls simultaneously — do not wait for one before starting the next. Each receives the final state only and may not edit.
- `solo` — skip; the artifact checks above are the verdict.

**The four gates (self-review in lean, spawned in full):**

1. **`creative-director`** — gate **CD-PHASE-GATE** (`../../docs/director-gates.md`)
2. **`technical-director`** — gate **TD-PHASE-GATE** (`../../docs/director-gates.md`)
3. **`producer`** — gate **PR-PHASE-GATE** (`../../docs/director-gates.md`)
4. **`art-director`** — gate **AD-PHASE-GATE** (`../../docs/director-gates.md`)

Pass to each: target phase name, list of artifacts present, and the context fields listed in that gate's definition.

**Collect all four responses, then present the Director Panel summary:**

```
## Director Panel Assessment

Creative Director:  [READY / CONCERNS / NOT READY]
  [feedback]

Technical Director: [READY / CONCERNS / NOT READY]
  [feedback]

Producer:           [READY / CONCERNS / NOT READY]
  [feedback]

Art Director:       [READY / CONCERNS / NOT READY]
  [feedback]
```

**Apply to the verdict:**
- Any director returns NOT READY → verdict is minimum FAIL. Director verdicts are advisory: the user may override with the risk recorded in the report; a deterministic gate exit `2` (`check_phase.py`, `verify_policy.py`) may not be overridden
- Any director returns CONCERNS → fix the items that carry a defect ticket (`rules/self-loop.md` § 2.1), record the rest as accepted concerns; verdict is minimum CONCERNS
- All four READY → eligible for PASS (still subject to artifact and quality checks from Section 3)

---

## 5. Output the Verdict

```
## Gate Check: [Current Phase] → [Target Phase]

**Date**: [date]
**Checked by**: gate-check skill

### Required Artifacts: [X/Y present]
- [x] design/gdd/game-concept.md — exists, 2.4KB
- [ ] docs/architecture/ — MISSING (no ADRs found)
- [x] production/sprints/ — exists, 1 sprint plan

### Quality Checks: [X/Y passing]
- [x] GDD has 8/8 required sections
- [ ] Tests — FAILED (3 failures in tests/unit/)
- [?] Core loop playtested — MANUAL CHECK NEEDED

### Blockers
1. **No Architecture Decision Records** — Run `$architecture-decision` to create one
   covering core system architecture before entering production.
2. **3 test failures** — Fix failing tests in tests/unit/ before advancing.

### Recommendations
- [Priority actions to resolve blockers]
- [Optional improvements that aren't blocking]

### Verdict: [PASS / CONCERNS / FAIL]
- **PASS**: All required artifacts present, all quality checks passing
- **CONCERNS**: Minor gaps exist but can be addressed during the next phase
- **FAIL**: Critical blockers must be resolved before advancing
```

---

## 5a. Chain-of-Verification

After drafting the verdict in Phase 5, challenge it before finalising.

**Step 1 — Generate 5 challenge questions** designed to disprove the verdict:

For a **PASS** draft:
- "Which quality checks did I verify by actually reading a file, vs. inferring they passed?"
- "Are there MANUAL CHECK NEEDED items I marked PASS without user confirmation?"
- "Did I confirm all listed artifacts have real content, not just empty headers?"
- "Could any blocker I dismissed as minor actually prevent the phase from succeeding?"
- "Which single check am I least confident in, and why?"

For a **CONCERNS** draft:
- "Could any listed CONCERN be elevated to a blocker given the project's current state?"
- "Is the concern resolvable within the next phase, or does it compound over time?"
- "Did I soften any FAIL condition into a CONCERN to avoid a harder verdict?"
- "Are there artifacts I didn't check that could reveal additional blockers?"
- "Do all the CONCERNS together create a blocking problem even if each is minor alone?"

For a **FAIL** draft:
- "Have I accurately separated hard blockers from strong recommendations?"
- "Are there any PASS items I was too lenient about?"
- "Am I missing any additional blockers the user should know about?"
- "Can I provide a minimal path to PASS — the specific 3 things that must change?"
- "Is the fail condition resolvable, or does it indicate a deeper design problem?"

**Step 2 — Answer each question** independently.
Do NOT reference the draft verdict text — re-check specific files; human-only items go into the Section 4 block.

**Step 3 — Revise if needed:**
- If any answer reveals a missed blocker → upgrade verdict (PASS→CONCERNS or CONCERNS→FAIL)
- If any answer reveals an over-stated blocker → downgrade only if citing specific evidence
- If answers are consistent → confirm verdict unchanged

**Step 4 — Note the verification** in the final report output:
`Chain-of-Verification: [N] questions checked — verdict [unchanged | revised from X to Y]`

---

## 6. Write the Report and Update Stage

Write the report from section 5 to `production/gate-checks/gate-check-[target-phase].md`
and report the path and the revert command.

- **PASS** → write the new stage name to `production/stage.txt` (single line, no
  trailing newline) and report the path and revert command
  (`git checkout -- production/stage.txt`). No confirmation question.
- **CONCERNS / FAIL** → do not touch `stage.txt`. Report what blocks. Director
  verdicts are advisory and the user may still advance with the risk recorded;
  a deterministic gate exit `2` is the only verdict nobody overrides.

Example: if passing the "Pre-Production → Production" gate:
```bash
echo -n "Production" > production/stage.txt
```

---

## 7. Closing Next Step

After the verdict and any `stage.txt` update, name the single recommended next
skill for the gate that ran. Recommend only; do not ask and do not run it.

- **systems-design PASS** → `$create-architecture` (required before any ADR: it produces the master architecture document and the prioritized ADR list)
- **technical-setup PASS** → begin Pre-Production prototyping of the Vertical Slice; `$architecture-decision [next-system]` if ADR gaps were listed
- **any other gate** → the first item of section 8 that applies to the verdict

---

## 8. Follow-Up Actions

Based on the verdict, suggest specific next steps. **Suggest only from the
resolved track's list** — offering `$art-bible` to a SaaS project is how a gate
loses the user's trust.

**Product track:**

- **No product concept?** → `$product-concept` to author it (`$create-prd` fails without it)
- **Concept exists but no feature PRDs?** → `$create-prd <feature>`, one per MVP-tier feature
- **PRDs not reviewed?** → `$design-review product/prd/prd-<feature>.md` (the catalog's `prd-review` step)
- **Stack not pinned?** → populate `.codex/studio/technical-preferences.md` (product-track equivalent of `$setup-engine`)
- **No architecture doc or ADRs?** → `$create-architecture`, then `$architecture-decision (×N)`
- **Paid API with no cost ceiling?** → `$api-cost-gate`
- **No analytics for the stated success metrics?** → instrument before Hardening; a metric with no event cannot be reported
- **Shipped features nobody has re-examined?** → `feature-viability` in the growth phase — keep / expand / patch / retire

**Game track:**

- **No art bible?** → `$art-bible` to create the visual identity specification
- **Art bible exists but no asset specs?** → `$asset-spec system:[name]` to generate per-asset visual specs and generation prompts from approved GDDs
- **No game concept?** → `$brainstorm` to create one
- **No systems index?** → `$map-systems` to decompose the concept into systems
- **Missing design docs?** → `$reverse-document` or delegate to `game-designer`
- **Small design change needed?** → `$quick-design` for changes under ~4 hours (bypasses full GDD pipeline)
- **No UX specs?** → `$ux-design [screen name]` to author specs, or `$team-ui [feature]` for full pipeline
- **UX specs not reviewed?** → `$ux-review [file]` or `$ux-review all` to validate
- **No accessibility requirements doc?** → write `design/accessibility-requirements.md` from the template at `../../docs/templates/accessibility-requirements.md`. Take tier `Basic` (remapping + subtitles) unless the concept, PRD or platform target names a higher one (`Standard` adds colorblind modes + scalable UI; `Comprehensive` adds motor accessibility + full settings menu; `Exemplary` adds an external audit). Name the tier and the reason in the report, with the path and revert command; the user can raise the tier later
- **No interaction pattern library?** → `$ux-design patterns` to initialize it
- **GDDs not cross-reviewed?** → `$review-all-gdds` (run after all MVP GDDs are individually approved)
- **Cross-GDD consistency issues?** → fix flagged GDDs, then re-run `$review-all-gdds`
- **No test framework?** → `$test-setup` to scaffold the framework for your engine
- **No QA plan for current sprint?** → `$qa-plan sprint` to generate one before implementation begins
- **Missing ADRs?** → `$architecture-decision` for individual decisions
- **No master architecture doc?** → `$create-architecture` for the full blueprint
- **ADRs missing engine compatibility sections?** → Re-run `$architecture-decision`
  or manually add Engine Compatibility sections to existing ADRs
- **Missing control manifest?** → `$create-control-manifest` (requires Accepted ADRs)
- **Missing epics?** → `$create-epics layer: foundation` then `$create-epics layer: core` (requires control manifest)
- **Missing stories for an epic?** → `$create-stories [epic-slug]` (run after each epic is created)
- **Stories not implementation-ready?** → `$story-readiness` to validate stories before developers pick them up
- **Tests failing?** → delegate to `lead-programmer` or `qa-tester`
- **No playtest data?** → `$playtest-report`
- **Less than 3 playtest sessions?** → Run more playtests before advancing. Use `$playtest-report` to structure findings.
- **No Difficulty Curve doc?** → Consider creating one at `design/difficulty-curve.md` before polish
- **No player journey document?** → create `design/player-journey.md` using the player journey template
- **Need a quick sprint check?** → `$sprint-status` for current sprint progress snapshot
- **Performance unknown?** → `$perf-profile`
- **Not localized?** → `$localize`
- **Ready for release?** → `$launch-checklist`

---

## Collaborative Protocol

This skill follows the collaborative design principle:

1. **Scan first**: check all artifacts and quality gates
2. **Ask about unknowns once**: one block after the checks; an unanswered item stays MANUAL CHECK NEEDED, never PASS
3. **Present findings**: show the full checklist with status
4. **Write and report**: the report goes to `production/gate-checks/`, `stage.txt` moves only on PASS; both paths come with a revert command
5. **Advisory except the deterministic gates**: the verdict is a recommendation. The user may advance despite CONCERNS or a director NOT READY, with the risk recorded in the report. `check_phase.py` / `verify_policy.py` exit `2` is not overridable here.
