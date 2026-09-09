---
name: architecture-decision
description: "Creates an Architecture Decision Record (ADR) documenting a significant technical decision, its context, alternatives considered, and consequences. Every major technical choice should have an ADR."
---

When this skill is invoked:

## 0. Parse Arguments — Detect Retrofit Mode

Resolve the review mode (once, store for all gate spawns this run):
1. If `--review [full|lean|solo]` was passed → use that
2. Else read `production/review-mode.txt` → use that value
3. Else → default to `lean`

See `../../docs/director-gates.md` for the full check pattern.

**If the argument starts with `retrofit` followed by a file path**
(e.g., `$architecture-decision retrofit docs/architecture/adr-0001-event-system.md`):

Enter **retrofit mode**:

1. Read the existing ADR file completely.
2. Identify which template sections are present by scanning headings:
   - `## Status` — **BLOCKING if missing**: `$story-readiness` cannot check ADR acceptance
   - `## ADR Dependencies` — HIGH if missing: dependency ordering breaks
   - `## Engine Compatibility` — HIGH if missing: post-cutoff risk unknown
   - `## GDD Requirements Addressed` — MEDIUM if missing: traceability lost
3. Present to the user:
   ```
   ## Retrofit: [ADR title]
   File: [path]

   Sections already present (will not be touched):
   ✓ Status: [current value, or "MISSING — will add"]
   ✓ [section]

   Missing sections to add:
   ✗ Status — BLOCKING (stories cannot validate ADR acceptance without this)
   ✗ ADR Dependencies — HIGH
   ✗ Engine Compatibility — HIGH
   ```
4. Add the [N] missing sections without modifying any existing content:
   - For **Status**: derive it. `Accepted` if the decision's named interfaces,
     classes or signals exist in the codebase; otherwise `Proposed`. Mark the
     value `[확인 필요]` in the report — never `Deprecated` or `Superseded` from
     evidence alone.
   - For **ADR Dependencies**: scan the other ADRs for references to this one
     and this one's references to them; write "None" for a field with no evidence.
   - For **Engine Compatibility**: read the engine reference docs (same as Step 0
     below), derive the domain from the Decision text, and generate the table
     with verified data.
   - For **GDD Requirements Addressed**: grep `design/gdd/` for the systems and
     interfaces the ADR names; list each hit with the requirement it satisfies.
     If nothing matches, write "None found `[확인 필요]`".
   - Append each missing section to the ADR file using the Edit tool.
   - **Never modify any existing section.** Only append or fill absent sections.
5. After adding all missing sections, update the ADR's `## Date` field if it is absent.
6. Report the path, the revert command (`git checkout -- <path>`), and every
   `[확인 필요]` value. Suggest: "Run `$architecture-review` to re-validate
   coverage now that this ADR has its Status and Dependencies fields."

If NOT in retrofit mode, proceed to Step 0 below (normal ADR authoring).

**No-argument guard**: If no argument was provided (title is empty), stop before
Phase 0 (K2 — the title cannot be derived from the repository):

> "Usage: `$architecture-decision <title>` — e.g., `event-system-architecture`,
> `physics-engine-choice`."

Verdict: **BLOCKED** — no decision title.

---

## 0. Load Engine Context (ALWAYS FIRST)

Before doing anything else, establish the engine environment:

1. Read `docs/engine-reference/[engine]/VERSION.md` to get:
   - Engine name and version
   - LLM knowledge cutoff date
   - Post-cutoff version risk levels (LOW / MEDIUM / HIGH)

2. Identify the **domain** of this architecture decision from the title or
   user description. Common domains: Physics, Rendering, UI, Audio, Navigation,
   Animation, Networking, Core, Input, Scripting.

3. Read the corresponding module reference if it exists:
   `docs/engine-reference/[engine]/modules/[domain].md`

4. Read `docs/engine-reference/[engine]/breaking-changes.md` — flag any
   changes in the relevant domain that post-date the LLM's training cutoff.

5. Read `docs/engine-reference/[engine]/deprecated-apis.md` — flag any APIs
   in the relevant domain that should not be used.

6. **Display a knowledge gap warning** before proceeding if the domain carries
   MEDIUM or HIGH risk:

   ```
   ⚠️  ENGINE KNOWLEDGE GAP WARNING
   Engine: [name + version]
   Domain: [domain]
   Risk Level: HIGH — This version is post-LLM-cutoff.

   Key changes verified from engine-reference docs:
   - [Change 1 relevant to this domain]
   - [Change 2]

   This ADR will be cross-referenced against the engine reference library.
   Proceed with verified information only — do NOT rely solely on training data.
   ```

   If no engine has been configured yet, prompt: "No engine is configured.
   Run `$setup-engine` first, or tell me which engine you are using."

---

## 1. Determine the next ADR number

Scan `docs/architecture/` for existing ADRs to find the next number.

---

## 2. Gather context

Read related code, existing ADRs, and relevant GDDs from `design/gdd/`.

### 2a: Architecture Registry Check (BLOCKING gate)

Read `docs/registry/architecture.yaml`. Extract entries relevant to this ADR's
domain and decision (grep by system name, domain keyword, or state being touched).

Present any relevant stances to the user **before** the collaborative design
begins, as locked constraints:

```
## Existing Architectural Stances (must not contradict)

State Ownership:
  player_health → owned by health-system (ADR-0001)
  Interface: HealthComponent.current_health (read-only float)
  → If this ADR reads or writes player health, it must use this interface.

Interface Contracts:
  damage_delivery → signal pattern (ADR-0003)
  Signal: damage_dealt(amount, target, is_crit)
  → If this ADR delivers or receives damage events, it must use this signal.

Forbidden Patterns:
  ✗ autoload_singleton_coupling (ADR-0001)
  ✗ direct_cross_system_state_write (ADR-0000)
  → The proposed approach must not use these patterns.
```

If the proposed decision would contradict any registered stance, surface the
conflict immediately:

> "⚠️ Conflict: This ADR proposes [X], but ADR-[NNNN] established that [Y] is
> the accepted pattern for this purpose. Proceeding without resolving this will
> produce contradictory ADRs and inconsistent stories."

Take (1) — align with the existing stance — unless the GDD requirement cannot be
met under it. Superseding an Accepted ADR (2) or declaring an exception (3)
reverses a settled decision (`rules/decision-lifecycle.md` § 4): that is K1.
Stop with Verdict: **BLOCKED** — conflict with ADR-[NNNN]; state both options,
the GDD evidence, and the cost of reverting each.

---

## 3. Guide the decision collaboratively

Derive the draft's assumptions from the context already gathered (GDDs read,
engine reference loaded, existing ADRs scanned). Record them; do not ask.

**Derive assumptions first:**
- **Problem**: Infer from the title + GDD context what decision needs to be made
- **Alternatives**: Propose 2-3 concrete options from engine reference + GDD requirements
- **Dependencies**: Scan existing ADRs for upstream dependencies; assume None if unclear
- **GDD linkage**: Extract which GDD systems the title directly relates to
- **Status**: Always `Proposed` for new ADRs — never ask the user what the status is

**Scope of assumptions**: Assumptions cover only: problem framing, alternative approaches, upstream dependencies, GDD linkage, and status. Schema design questions (e.g., "How should spawn timing work?", "Should data be inline or external?") are NOT assumptions — they are design decisions, made separately after the assumptions are recorded.

**Record the assumptions block** in the report and as an `Assumptions` note under the ADR's Context section:

```
Assumptions behind this draft:

Problem: [one-sentence problem statement derived from context]
Alternatives considered:
  A) [option derived from engine reference]
  B) [option derived from GDD requirements]
  C) [option from common patterns]
GDD systems driving this: [list derived from context]
Dependencies: [upstream ADRs if any, otherwise "None"]
Status: Proposed
```

An assumption that could go either way gets `[확인 필요]` next to it; the closing report lists them together.

**Schema and data design choices**: decide each one — take the option the engine reference recommends, else the one the GDD requirement implies. Record the decision and the rejected option in the Alternatives section.

**After engine specialist and TD reviews return** (Step 4.5/4.6), decide any unresolved point by the same rule. If two options tie and the choice is hard to reverse (R3+, `rules/verify-route.md`), pick the one closer to the existing registry stances, mark it `[확인 필요]` in the ADR, and list it in the closing report.

**ADR Dependencies** — derive from existing ADRs and record:
- Does this decision depend on any other ADR not yet Accepted?
- Does it unlock or unblock any other ADR or epic?
- Does it block any specific epic from starting?

Record answers in the **ADR Dependencies** section. Write "None" for each field if no constraints apply.

---

## 4. Generate the ADR

Following this format:

```markdown
# ADR-[NNNN]: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXXX]

## Date
[Date of decision]

## Engine Compatibility

| Field | Value |
|-------|-------|
| **Engine** | [e.g. Godot 4.6] |
| **Domain** | [Physics / Rendering / UI / Audio / Navigation / Animation / Networking / Core / Input] |
| **Knowledge Risk** | [LOW / MEDIUM / HIGH — from VERSION.md] |
| **References Consulted** | [List engine-reference docs read, e.g. `docs/engine-reference/godot/modules/physics.md`] |
| **Post-Cutoff APIs Used** | [Any APIs from post-LLM-cutoff versions this decision depends on, or "None"] |
| **Verification Required** | [Specific behaviours to test before shipping, or "None"] |

## ADR Dependencies

| Field | Value |
|-------|-------|
| **Depends On** | [ADR-NNNN (must be Accepted before this can be implemented), or "None"] |
| **Enables** | [ADR-NNNN (this ADR unlocks that decision), or "None"] |
| **Blocks** | [Epic/Story name — cannot start until this ADR is Accepted, or "None"] |
| **Ordering Note** | [Any sequencing constraint that isn't captured above] |

## Context

### Problem Statement
[What problem are we solving? Why does this decision need to be made now?]

### Constraints
- [Technical constraints]
- [Timeline constraints]
- [Resource constraints]
- [Compatibility requirements]

### Requirements
- [Must support X]
- [Must perform within Y budget]
- [Must integrate with Z]

## Decision

[The specific technical decision made, described in enough detail for someone
to implement it.]

### Architecture Diagram
[ASCII diagram or description of the system architecture this creates]

### Key Interfaces
[API contracts or interface definitions this decision creates]

## Alternatives Considered

### Alternative 1: [Name]
- **Description**: [How this would work]
- **Pros**: [Advantages]
- **Cons**: [Disadvantages]
- **Rejection Reason**: [Why this was not chosen]

### Alternative 2: [Name]
- **Description**: [How this would work]
- **Pros**: [Advantages]
- **Cons**: [Disadvantages]
- **Rejection Reason**: [Why this was not chosen]

## Consequences

### Positive
- [Good outcomes of this decision]

### Negative
- [Trade-offs and costs accepted]

### Risks
- [Things that could go wrong]
- [Mitigation for each risk]

## GDD Requirements Addressed

| GDD System | Requirement | How This ADR Addresses It |
|------------|-------------|--------------------------|
| [system-name].md | [specific rule, formula, or performance constraint from that GDD] | [how this decision satisfies it] |

## Performance Implications
- **CPU**: [Expected impact]
- **Memory**: [Expected impact]
- **Load Time**: [Expected impact]
- **Network**: [Expected impact, if applicable]

## Migration Plan
[If this changes existing code, how do we get from here to there?]

## Validation Criteria
[How will we know this decision was correct? What metrics or tests?]

## Related Decisions
- [Links to related ADRs]
- [Links to related design documents]
```

4.5. **Engine Specialist Validation** — Before saving, spawn the **primary engine specialist** as a Codex subagent to validate the drafted ADR:
   - Read `.codex/studio/technical-preferences.md` `Engine Specialists` section to get the primary specialist
   - If no engine is configured (`[TO BE CONFIGURED]`), skip this step
   - Spawn `subagent_type: [primary specialist]` with: the ADR's Engine Compatibility section, Decision section, Key Interfaces, and the engine reference docs path. Ask them to:
     1. Confirm the proposed approach is idiomatic for the pinned engine version
     2. Flag any APIs or patterns that are deprecated or changed post-training-cutoff
     3. Identify engine-specific risks or gotchas not captured in the current ADR draft
   - If the specialist identifies a **blocking issue** (wrong API, deprecated approach, engine version incompatibility): revise the Decision and Engine Compatibility sections accordingly and record the revision, with the specialist's evidence, in the report
   - If the specialist finds **minor notes** only: incorporate them into the ADR's Risks subsection

**Review mode check** — apply before spawning TD-ADR:
- `solo` → skip. Note: "TD-ADR skipped — Solo mode." Proceed to Step 4.7 (GDD sync check).
- `lean` → skip (not a PHASE-GATE). Note: "TD-ADR skipped — Lean mode." Proceed to Step 4.7 (GDD sync check).
- `full` → spawn as normal.

4.6. **Technical Director Strategic Review** — After the engine specialist validation, spawn `technical-director` as a Codex subagent using gate **TD-ADR** (`../../docs/director-gates.md`):
   - Pass: the ADR file path (or draft content), engine version, domain, any existing ADRs in the same domain
   - The TD validates architectural coherence (is this decision consistent with the whole system?) — distinct from the engine specialist's API-level check
   - If CONCERNS or REJECT: revise the Decision or Alternatives sections accordingly before proceeding

4.7. **GDD Sync Check** — Before writing, scan all GDDs
referenced in the "GDD Requirements Addressed" section for naming inconsistencies
with the ADR's Key Interfaces and Decision sections (renamed signals, API methods,
or data types). If any are found, surface them as a **prominent warning block**
immediately before writing — not as a footnote:

```
⚠️ GDD SYNC REQUIRED
[gdd-filename].md uses names this ADR has renamed:
  [old_name] → [new_name_from_adr]
  [old_name_2] → [new_name_2_from_adr]
The GDD must be updated before or alongside writing this ADR to prevent
developers reading the GDD from implementing the wrong interface.
```

If no inconsistencies: skip this block silently.

5. **Write** the ADR to `docs/architecture/adr-[NNNN]-[slug].md`, creating the
directory if needed. If GDD sync issues were found, update the GDD file(s) to use
the new names in the same pass. Report every path written and its revert command
(`git checkout -- <path>`). This is the one document-level review point: the
report shows the full draft.

6. **Update Architecture Registry**

Scan the written ADR for new architectural stances that should be registered:
- State it claims ownership of
- Interface contracts it defines (signal signatures, method APIs)
- Performance budget it claims
- API choices it makes explicitly
- Patterns it bans (Consequences → Negative or explicit "do not use X")

Present candidates:
```
Registry candidates from this ADR:
  NEW state ownership:      player_stamina → stamina-system
  NEW interface contract:   stamina_depleted signal
  NEW performance budget:   stamina-system: 0.5ms/frame
  NEW forbidden pattern:    polling stamina each frame (use signal instead)
  EXISTING (referenced_by update only): player_health → already registered ✅
```

**Registry append logic**: When writing to `docs/registry/architecture.yaml`, do NOT assume sections are empty. The file may already have entries from previous ADRs written in this session. Before each Edit call:
1. Read the current state of `docs/registry/architecture.yaml`
2. Find the correct section (state_ownership, interfaces, forbidden_patterns, api_decisions)
3. Append the new entry AFTER the last existing entry in that section — do not try to replace a `[]` placeholder that may no longer exist
4. If the section has entries already, use the closing content of the last entry as the `old_string` anchor, and append the new entry after it

Append the new entries to `docs/registry/architecture.yaml` and report the path
with its revert command. Never modify existing entries — a stance that changes
was resolved as a K1 conflict in Step 2; only then set the old entry to
`status: superseded_by: ADR-[NNNN]` and add the new entry.

---

## 7. Closing Next Steps

After the ADR is written and the registry updated, close with a report.

Before writing the closing block:
1. Read `docs/registry/architecture.yaml` — check if any priority ADRs are still unwritten (look for ADRs flagged in technical-preferences.md or systems-index.md as prerequisites)
2. Check if all prerequisite ADRs are now written. If yes, name `$design-system [first-undesigned-system]` as the recommended next step.
3. List ALL remaining priority ADRs — not just the next one or two.

Closing block:
```
ADR-[NNNN] written and registry updated.
Paths: [each path — revert: git checkout -- <path>]
Confirm items ([확인 필요]): [list, or "None"]
Recommended next: `$architecture-decision [next-priority-adr-name]` — [brief description]
Remaining priority ADRs: [all of them, with one line each]
```

If there are no remaining priority ADRs and no undesigned GDD systems, recommend `$architecture-review` in a fresh session.

**Always include this fixed notice in the closing output (do NOT omit it):**

> To validate ADR coverage against your GDDs, open a **fresh Codex session**
> and run `$architecture-review`.
>
> **Never run `$architecture-review` in the same session as `$architecture-decision`.**
> The reviewing agent must be independent of the authoring context to give an unbiased
> assessment. Running it here would invalidate the review.

Update any stories that were `Status: Blocked` pending this ADR to `Status: Ready`.
