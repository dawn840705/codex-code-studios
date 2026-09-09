---
name: create-architecture
description: "Guided, section-by-section authoring of the master architecture document for the game. Reads all GDDs, the systems index, existing ADRs, and the engine reference library to produce a complete architecture blueprint before any code is written. Engine-version-aware: flags knowledge gaps and validates decisions against the pinned engine version."
---

> **Track check — this skill is game-framed.** Resolve `production/track.txt` (or the
> session's `PROJECT_TYPE` line) before Phase 0.
>
> - **`game`** — run as written.
> - **`product`** (web / mobile / service) — substitute as you read: player becomes user,
>   game becomes product, GDD becomes PRD (`design/gdd/` → `product/prd/`), engine becomes
>   the stack pinned in `.codex/studio/technical-preferences.md`. Read `product/prd/product-concept.md` and every `product/prd/prd-*.md` in place of `design/gdd/game-concept.md` and the GDDs. There is no systems-index; the concept's scope tiers bound the layers. The engine section becomes the pinned stack — framework, hosting, data store.
> - **Unresolved** — ask once which track this is, write the answer to `production/track.txt`,
>   then continue. A greenfield project has no signal either way; do not infer one from the
>   repository contents.

# Create Architecture

This skill produces `docs/architecture/architecture.md` — the master architecture
document that translates all approved GDDs into a concrete technical blueprint.
It sits between design and implementation, and must exist before sprint planning begins.

**Distinct from `$architecture-decision`**: ADRs record individual point decisions.
This skill creates the whole-system blueprint that gives ADRs their context.

Resolve the review mode (once, store for all gate spawns this run):
1. If `--review [full|lean|solo]` was passed → use that
2. Else read `production/review-mode.txt` → use that value
3. Else → default to `lean`

See `../../docs/director-gates.md` for the full check pattern.

**Argument modes:**
- **No argument / `full`**: Full guided walkthrough — all sections, start to finish
- **`layers`**: Focus on the system layer diagram only
- **`data-flow`**: Focus on data flow between modules only
- **`api-boundaries`**: Focus on API boundary definitions only
- **`adr-audit`**: Audit existing ADRs for engine compatibility gaps only

---

## Phase 0: Load All Context

Before anything else, load the full project context in this order:

### 0a. Engine Context (Critical)

Read the engine reference library completely:

1. `docs/engine-reference/[engine]/VERSION.md`
   → Extract: engine name, version, LLM cutoff, post-cutoff risk levels
2. `docs/engine-reference/[engine]/breaking-changes.md`
   → Extract: all HIGH and MEDIUM risk changes
3. `docs/engine-reference/[engine]/deprecated-apis.md`
   → Extract: APIs to avoid
4. `docs/engine-reference/[engine]/current-best-practices.md`
   → Extract: post-cutoff best practices that differ from training data
5. All files in `docs/engine-reference/[engine]/modules/`
   → Extract: current API patterns per domain

If no engine is configured, stop and prompt:
> "No engine is configured. Run `$setup-engine` first. Architecture cannot be
> written without knowing which engine and version you are targeting."

### 0b. Design Context + Technical Requirements Extraction

Read all approved design documents and extract technical requirements from each:

1. `design/gdd/game-concept.md` — game pillars, genre, core loop
2. `design/gdd/systems-index.md` — all systems, dependencies, priority tiers
3. `.codex/studio/technical-preferences.md` — naming conventions, performance budgets,
   allowed libraries, forbidden patterns
4. **Every GDD in `design/gdd/`** — for each, extract technical requirements:
   - Data structures implied by the game rules
   - Performance constraints stated or implied
   - Engine capabilities the system requires
   - Cross-system communication patterns (what talks to what, how)
   - State that must persist (save/load implications)
   - Threading or timing requirements

Build a **Technical Requirements Baseline** — a flat list of all extracted
requirements across all GDDs, numbered `TR-[gdd-slug]-[NNN]`. This is the
complete set of what the architecture must cover. Present it as:

```
## Technical Requirements Baseline
Extracted from [N] GDDs | [X] total requirements

| Req ID | GDD | System | Requirement | Domain |
|--------|-----|--------|-------------|--------|
| TR-combat-001 | combat.md | Combat | Hitbox detection per-frame | Physics |
| TR-combat-002 | combat.md | Combat | Combo state machine | Core |
| TR-inventory-001 | inventory.md | Inventory | Item persistence | Save/Load |
```

This baseline feeds into every subsequent phase. No GDD requirement should be
left without an architectural decision to support it by the end of this session.

### 0c. Existing Architecture Decisions

Read all files in `docs/architecture/` to understand what has already been decided.
List any ADRs found and their domains.

### 0d. Generate Knowledge Gap Inventory

Before proceeding, display a structured summary:

```
## Engine Knowledge Gap Inventory
Engine: [name + version]
LLM Training Covers: up to approximately [version]
Post-Cutoff Versions: [list]

### HIGH RISK Domains (must verify against engine reference before deciding)
- [Domain]: [Key changes]

### MEDIUM RISK Domains (verify key APIs)
- [Domain]: [Key changes]

### LOW RISK Domains (in training data, likely reliable)
- [Domain]: [no significant post-cutoff changes]

### Systems from GDD that touch HIGH/MEDIUM risk domains:
- [GDD system name] → [domain] → [risk level]
```

Record the inventory in the report ("[N] systems in HIGH RISK engine domains")
and continue building the architecture with these warnings flagged throughout.

---

## Phase 1: System Layer Mapping

Map every system from `systems-index.md` into an architecture layer. The standard
game architecture layers are:

```
┌─────────────────────────────────────────────┐
│  PRESENTATION LAYER                         │  ← UI, HUD, menus, VFX, audio
├─────────────────────────────────────────────┤
│  FEATURE LAYER                              │  ← gameplay systems, AI, quests
├─────────────────────────────────────────────┤
│  CORE LAYER                                 │  ← physics, input, combat, movement
├─────────────────────────────────────────────┤
│  FOUNDATION LAYER                           │  ← engine integration, save/load,
│                                             │    scene management, event bus
├─────────────────────────────────────────────┤
│  PLATFORM LAYER                             │  ← OS, hardware, engine API surface
└─────────────────────────────────────────────┘
```

For each GDD system, ask:
- Which layer does it belong to?
- What are its module boundaries?
- What does it own exclusively? (data, state, behaviour)

Write the layer map immediately to the skeleton file. Record the assignments in
the report, with the rejected alternative for any system that could sit in two
layers, marked `[확인 필요]`.

**Engine awareness check**: For each system assigned to the Core and Foundation
layers, flag if it touches a HIGH or MEDIUM risk engine domain. Show the relevant
engine reference excerpt inline.

---

## Phase 2: Module Ownership Map

For each module defined in Phase 1, define ownership:

- **Owns**: what data and state this module is solely responsible for
- **Exposes**: what other modules may read or call
- **Consumes**: what it reads from other modules
- **Engine APIs used**: which specific engine classes/nodes/signals this module
  calls directly (with version and risk level noted)

Format as a table per layer, then as an ASCII dependency diagram.

**Engine awareness check**: For every engine API listed, verify against the
relevant module reference doc. If an API is post-cutoff, flag it:

```
⚠️  [ClassName.method()] — Godot 4.6 (post-cutoff, HIGH risk)
    Verified against: docs/engine-reference/godot/modules/[domain].md
    Behaviour confirmed: [yes / NEEDS VERIFICATION]
```

Write the ownership map to the skeleton file. Mark any ownership that could go
either way `[확인 필요]` and name the alternative owner.

---

## Phase 3: Data Flow

Define how data moves between modules during key game scenarios. Cover at minimum:

1. **Frame update path**: Input → Core systems → State → Rendering
2. **Event/signal path**: How systems communicate without tight coupling
3. **Save/load path**: What state is serialised, which module owns serialisation
4. **Initialisation order**: Which modules must boot before others

Use ASCII sequence diagrams where helpful. For each data flow:
- Name the data being transferred
- Identify the producer and consumer
- State whether this is synchronous call, signal/event, or shared state
- Flag any data flows that cross thread boundaries

Write each scenario to the skeleton file as it is completed.

---

## Phase 4: API Boundaries

Define the public contracts between modules. For each boundary:

- What is the interface a module exposes to the rest of the system?
- What are the entry points (functions/signals/properties)?
- What invariants must callers respect?
- What must the module guarantee to callers?

Write in pseudocode or the project's actual language (from technical preferences).
These become the contracts programmers implement against.

**Engine awareness check**: If any interface uses engine-specific types (e.g.
`Node`, `Resource`, `Signal` in Godot), flag the version and verify the type
exists and has not changed signature in the target engine version.

---

## Phase 5: ADR Audit + Traceability Check

Review all existing ADRs from Phase 0c against both the architecture built in
Phases 1-4 AND the Technical Requirements Baseline from Phase 0b.

### ADR Quality Check

For each ADR:
- [ ] Does it have an Engine Compatibility section?
- [ ] Is the engine version recorded?
- [ ] Are post-cutoff APIs flagged?
- [ ] Does it have a "GDD Requirements Addressed" section?
- [ ] Does it conflict with the layer/ownership decisions made in this session?
- [ ] Is it still valid for the pinned engine version?

| ADR | Engine Compat | Version | GDD Linkage | Conflicts | Valid |
|-----|--------------|---------|-------------|-----------|-------|
| ADR-0001: [title] | ✅/❌ | ✅/❌ | ✅/❌ | None/[conflict] | ✅/⚠️ |

### Traceability Coverage Check

Map every requirement from the Technical Requirements Baseline to existing ADRs.
For each requirement, check if any ADR's "GDD Requirements Addressed" section
or decision text covers it:

| Req ID | Requirement | ADR Coverage | Status |
|--------|-------------|--------------|--------|
| TR-combat-001 | Hitbox detection per-frame | ADR-0003 | ✅ |
| TR-combat-002 | Combo state machine | — | ❌ GAP |

Count: X covered, Y gaps. For each gap, it becomes a **Required New ADR**.

### Required New ADRs

List all decisions made during this architecture session (Phases 1-4) that do
not yet have a corresponding ADR, PLUS all uncovered Technical Requirements.
Group by layer — Foundation first:

**Foundation Layer (must create before any coding):**
- `$architecture-decision [title]` → covers: TR-[id], TR-[id]

**Core Layer:**
- `$architecture-decision [title]` → covers: TR-[id]

---

## Phase 6: Missing ADR List

Based on the full architecture, produce a complete list of ADRs that should exist
but don't yet. Group by priority:

**Must have before coding starts (Foundation & Core decisions):**
- [e.g. "Scene management and scene loading strategy"]
- [e.g. "Event bus vs direct signal architecture"]

**Should have before the relevant system is built:**
- [e.g. "Inventory serialisation format"]

**Can defer to implementation:**
- [e.g. "Specific shader technique for water"]

---

## Phase 7: Write the Master Architecture Document

Once all sections are written, assemble the complete document at
`docs/architecture/architecture.md`. Report the path and the revert command
(`git checkout -- docs/architecture/architecture.md`). This is the one
document-level review point: the report shows the section list and every
`[확인 필요]` item.

The document structure:

```markdown
# [Game Name] — Master Architecture

## Document Status
- Version: [N]
- Last Updated: [date]
- Engine: [name + version]
- GDDs Covered: [list]
- ADRs Referenced: [list]

## Engine Knowledge Gap Summary
[Condensed from Phase 0d inventory — HIGH/MEDIUM risk domains and their implications]

## System Layer Map
[From Phase 1]

## Module Ownership
[From Phase 2]

## Data Flow
[From Phase 3]

## API Boundaries
[From Phase 4]

## ADR Audit
[From Phase 5]

## Required ADRs
[From Phase 6]

## Architecture Principles
[3-5 key principles that govern all technical decisions for this project,
derived from the game concept, GDDs, and technical preferences]

## Open Questions
[Decisions deferred — must be resolved before the relevant layer is built]
```

---

## Phase 7b: Technical Director Sign-Off + Lead Programmer Feasibility Review

After writing the master architecture document, perform an explicit sign-off before handoff.

**Step 1 — Technical Director self-review** (this skill runs as technical-director):

Apply gate **TD-ARCHITECTURE** (`../../docs/director-gates.md`) as a self-review. Check all four criteria from that gate definition against the completed document.

**Review mode check** — apply before spawning LP-FEASIBILITY:
- `solo` → skip. Note: "LP-FEASIBILITY skipped — Solo mode." Proceed to Phase 8 handoff.
- `lean` → skip (not a PHASE-GATE). Note: "LP-FEASIBILITY skipped — Lean mode." Proceed to Phase 8 handoff.
- `full` → spawn the named director as a separate reviewing subagent (read-only, final state only; `docs/director-gates.md`).

**Step 2 — Spawn `lead-programmer` as a Codex subagent using gate LP-FEASIBILITY (`../../docs/director-gates.md`):**

Pass: architecture document path, technical requirements baseline summary, ADR list.

**Step 3 — Apply both assessments:**

Show the Technical Director assessment and Lead Programmer verdict side by side in the report, then:
- APPROVE / FEASIBLE → proceed to handoff.
- CONCERNS → fix every flagged item that names a section and evidence (a defect ticket), record each fix, and proceed. The remainder is advisory and stays listed in the report.
- REJECT / INFEASIBLE → revise the flagged sections and re-spawn the gate within the `$self-loop` limits (`rules/self-loop.md`). If it still rejects: Verdict: **BLOCKED** — list the open items.

**Step 4 — Record sign-off in the architecture document:**

Update the Document Status section:
```
- Technical Director Sign-Off: [date] — APPROVED / APPROVED WITH CONDITIONS
- Lead Programmer Feasibility: FEASIBLE / CONCERNS ACCEPTED / REVISED
```

Update the Document Status section in `docs/architecture/architecture.md` with the sign-off and report it with the document path.

---

## Phase 8: Handoff

After writing the document, provide a clear handoff:

1. **Run these ADRs next** (from Phase 6, prioritised): list the top 3
2. **Gate check**: "The master architecture document is complete. Run `$gate-check
   pre-production` when all required ADRs are also written."
3. **Update session state**: Write a summary to `production/session-state/active.md`

---

## Collaborative Protocol

This skill follows the collaborative design principle at every phase:

1. **Load context silently** — do not narrate file reads
2. **Show findings** — the knowledge gap inventory and layer proposals go in the report
3. **Decide and record** — for each architectural choice take the option the
   engine reference and existing ADRs support; record the alternatives with
   pros/cons. A tie that is hard to reverse (R3+) is marked `[확인 필요]`
4. **Write, then report** — every section lands in the file; the report lists
   the path, the revert command, and every `[확인 필요]` item
5. **Incremental writing** — write each section immediately; do not accumulate
   everything and write at the end. This survives session crashes.

Binding architectural decisions are made in ADRs (`$architecture-decision`), not
here: this document proposes, the ADR decides. Where two options tie, record both
with pros/cons and mark the choice `[확인 필요]`.

---

## Recommended Next Steps

- Run `$architecture-decision [title]` for each required ADR listed in Phase 6 — Foundation layer ADRs first
- Run `$create-control-manifest` once the required ADRs are written to produce the layer rules manifest
- Run `$gate-check pre-production` when all required ADRs are written and the architecture is signed off
