---
name: reverse-document
description: "Generate design or architecture documents from existing implementation. Works backwards from code/prototypes to create missing planning docs."
# Read-only diagnostic skill — no specialist agent delegation needed
---

# Reverse Documentation

This skill analyzes existing implementation (code, prototypes, systems) and generates
appropriate design or architecture documentation. Use this when:
- You built a feature without writing a design doc first
- You inherited a codebase without documentation
- You prototyped a mechanic and need to formalize it
- You need to document "why" behind existing code

Writes: `design/gdd/[system-name].md`, `docs/architecture/[decision-name].md`, or `prototypes/[name]/CONCEPT.md` — one document per run, chosen by `<type>` (Phase 5 table); the analyzed source is never modified.

---

## Workflow

## Phase 1: Parse Arguments

**Format**: `$reverse-document <type> <path>`

**Type options**:
- `design` → Generate a game design document (GDD section)
- `architecture` → Generate an Architecture Decision Record (ADR)
- `concept` → Generate a concept document from prototype

**Path**: Directory or file to analyze
- `src/gameplay/combat/` → All combat-related code
- `src/core/event-system.cpp` → Specific file
- `prototypes/stealth-mech/` → Prototype directory

**Examples**:
```bash
$reverse-document design src/gameplay/magic-system
$reverse-document architecture src/core/entity-component
$reverse-document concept prototypes/vehicle-combat
```

## Phase 2: Analyze Implementation

**Read and understand the code/prototype**:

**For design docs (GDD):**
- Identify mechanics, rules, formulas
- Extract gameplay values (damage, cooldowns, ranges)
- Find state machines, ability systems, progression
- Detect edge cases handled in code
- Map dependencies (what systems interact?)

**For architecture docs (ADR):**
- Identify patterns (ECS, singleton, observer, etc.)
- Understand technical decisions (threading, serialization, etc.)
- Map dependencies and coupling
- Assess performance characteristics
- Find constraints and trade-offs

**For concept docs (prototype analysis):**
- Identify core mechanic
- Extract emergent gameplay patterns
- Note what worked vs what didn't
- Find technical feasibility insights
- Document player fantasy / feel

## Phase 3: Resolve Intent

**DO NOT** just describe the code. Recover the "why" from the repository first —
commit messages, code comments, ADRs, prior design notes, prototype READMEs. What
the repository cannot answer goes into the document as `Assumption: …` with the
reading you chose, and into the report as a question for the author. Do not wait
for the answer; the document is R and the assumption is easy to correct.

Questions worth an `Assumption:` line —

**Design questions**:
- "I see a [resource] system that depletes during [activity]. Was this for:
  - Pacing (prevent spam)?
  - Resource management (strategic depth)?
  - Or something else?"
- "The [mechanic] seems central. Is this a core pillar, or supporting feature?"
- "[Value] scales exponentially with [factor]. Intentional design, or needs rebalancing?"

**Architecture questions**:
- "You're using a service locator pattern. Was this chosen for:
  - Testability (mock dependencies)?
  - Decoupling (reduce hard references)?
  - Or inherited from existing code?"
- "I see manual memory management instead of smart pointers. Performance requirement, or legacy?"

**Concept questions**:
- "The prototype emphasizes stealth over combat. Is that the intended pillar?"
- "Players seem to exploit the grappling hook for speed. Feature or bug?"

## Phase 4: Record Findings

Open the report with what you discovered:

```
Analyzed [path]/:

MECHANICS IMPLEMENTED:
- [mechanic-a] with [property] (e.g. timing windows, cooldowns)
- [mechanic-b] (e.g. interaction between two states)
- [resource] system (depletes on [action], regens on [condition])
- [state] system (builds up, triggers [effect])

FORMULAS DISCOVERED:
- [Output] = [formula using discovered variables]
- [Secondary output] = [formula]

ASSUMPTIONS (repository gave no answer — correct me in the doc):
1. [Resource] system — read as pacing; alternative: resource management
2. [Mechanic] — read as core pillar; alternative: supporting feature
3. [Value] scaling — read as intentional; alternative: needs tuning
```

## Phase 5: Draft Document Using Template

Based on type, use appropriate template:

| Type | Template | Output Path |
|------|----------|-------------|
| `design` | `templates/design-doc-from-implementation.md` | `design/gdd/[system-name].md` |
| `architecture` | `templates/architecture-doc-from-code.md` | `docs/architecture/[decision-name].md` |
| `concept` | `templates/concept-doc-from-prototype.md` | `prototypes/[name]/CONCEPT.md` or `design/concepts/[name].md` |

**Draft structure**:
- Capture **what exists** (mechanics, patterns, implementation)
- Document **why it exists** (intent from the repository, or `Assumption:`)
- Identify **what's missing** (edge cases not handled, gaps in design)
- Flag **follow-up work** (balance tuning, missing features)

## Phase 6: Explain the Draft

Put this in the report next to the path:
```
ADDITIONS I MADE:
- Documented [mechanic] as "[intent]" (source: [commit/comment], or Assumption)
- Added edge cases not in code (e.g., what if [resource] hits 0 mid-[action]?)
- Flagged balance concern: [scaling type] scaling at [boundary condition]

SECTIONS MARKED AS INCOMPLETE:
- "[System] interaction with [other-system]" (not fully implemented yet)
- "[Variant or feature]" (only [subset] implemented so far)
```

## Phase 7: Write Document with Metadata

Write the file (path from the Phase 5 table; never overwrite an existing document —
write `[name].reverse.md` beside it and say so) with special markers:

```markdown
---
status: reverse-documented
source: [path/]
date: [today]
verified-by: [pending — see Assumptions]
---

# [System Name] Design

> **Note**: This document was reverse-engineered from the existing implementation.
> It captures current behavior and clarified design intent. Some sections may be
> incomplete where implementation is partial or intent was unclear.

[Rest of document...]
```

## Phase 8: Flag Follow-Up Work

After writing, report:

```
✅ Written to design/gdd/combat-system.md (revert: git checkout -- design/gdd/combat-system.md)
Verdict: COMPLETE — [N] assumptions await the author's correction

FOLLOW-UP RECOMMENDED:
1. Run $balance-check on combat formulas (exponential scaling concern)
2. Create ADR for stamina system architecture decision
3. Implement missing edge cases:
   - Stamina depletion mid-combo behavior
   - Stagger state during dodge
4. Extend design doc when weapon variety is implemented
```

Do not run the follow-ups; the user picks.

---

## Template Selection Logic

| If analyzing... | Use template... | Because... |
|----------------|-----------------|------------|
| `src/gameplay/*` | design-doc-from-implementation.md | Gameplay mechanics → GDD |
| `src/core/*`, `src/ai/*` | architecture-doc-from-code.md | Core systems → ADR |
| `prototypes/*` | concept-doc-from-prototype.md | Experiments → concept doc |
| `src/networking/*` | architecture-doc-from-code.md | Technical systems → ADR |
| `src/ui/*` | design-doc-from-implementation.md | UI/UX → design spec |

---

## Example Session: Reverse-Document a System

```
User: $reverse-document design src/gameplay/[system]

Agent: I'll analyze your [system] implementation to create a design doc.
       [Reads code, discovers mechanics, formulas]

Agent: Analyzed src/gameplay/[system]/ — [mechanics, formulas].
       Intent from git log: [resource] added in [commit] "prevent [unwanted behavior]" → pacing.
       Assumptions (no source found): [mechanic] read as core pillar; [value] scaling read as intentional.

       ✅ Written to design/gdd/[system-name].md (revert: git checkout -- design/gdd/[system-name].md)
       ✅ Marked as [REVERSE-DOCUMENTED], verified-by pending
       ✅ Flagged [value] scaling for rebalancing

       Please correct the two assumptions in the doc if they are wrong.
       Next steps:
       - Run $balance-check to validate [curve]
       - Document [mechanic] as core pillar in game-pillars.md
```

---

## Collaborative Protocol

This skill follows the collaborative design principle:

1. **Analyze First**: Read code, understand implementation
2. **Recover Intent**: "why" from commits, comments, ADRs — not just "what"
3. **Mark Assumptions**: what the repository cannot answer is written as `Assumption:`, never as fact
4. **Draft Document**: reality + intent + assumptions
5. **Write and Report**: path, revert command, additions, assumptions. Verdict: **COMPLETE** — document generated. **BLOCKED** only when the path does not exist or the type is missing (K2).
6. **Flag Follow-Up**: Suggest related work, don't auto-execute

**Never present an assumption as intent. Label it, and let the author correct it.**
