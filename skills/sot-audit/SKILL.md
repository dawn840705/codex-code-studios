---
name: sot-audit
description: "Audit a Single Source of Truth (SoT) for cross-witness consistency. Use when a system is defined in multiple places (design doc, code enum, engine asset, runtime usage) and you need to detect silent-fail mismatches before they cause runtime bugs. Use when user says 'audit the SoT', 'check FSM consistency', 'find drift in X', 'is X consistent across doc/code/engine'."
---

## Purpose

Many game systems have **one logical specification** but are *physically defined or referenced* in 3-5 separate places. When those witnesses drift apart, you get **silent-fail bugs** — the engine ignores a missing parameter without throwing, a transition condition references a stale name, a doc promises behaviour the code never implemented.

Examples of multi-witness systems:
- **Player FSM**: design doc + enum + Animator controller + state-change call sites (4 witnesses)
- **Input bindings**: action asset + reader callbacks + property surface + usage sites + doc (5 witnesses)
- **Save data**: schema doc + serializer struct + migration table + UI references (4 witnesses)
- **Localization keys**: source-of-truth CSV + code lookup calls + UI prefab references (3 witnesses)

This skill produces a **N-way mismatch matrix** with severity classifications, so you can fix high-severity silent-fails first.

Read-only: writes nothing — the mismatch matrix is returned in the conversation; no witness file is edited.

---

## Phase 1: Identify the SoT and its witnesses

From `the first invocation argument`, determine the SoT name (e.g. "player-fsm", "input-bindings", "save-schema").

If witness paths are given as `key=value` args, use them. Otherwise, ask the user to enumerate all witnesses, e.g.:

> Where is `<sot-name>` *defined or referenced*? Provide each path. Examples:
> - `design/specs/player-fsm.md` (canonical spec)
> - `src/PlayerStateType.cs` (enum)
> - `assets/animator/PlayerAnim.controller` (engine asset)
> - `src/PlayerController.cs` (call sites — pass the directory, not just one file)

Confirm the **canonical** witness (the one that "wins" in case of conflict — usually the design doc or asset file).

---

## Phase 2: Read all witnesses in parallel

Use parallel `Read` / `Grep` calls. For large engine assets (Unity `.controller`, Godot `.tscn`), use targeted Grep instead of full Read.

For **call-site witnesses** (e.g. `PlayerController.cs`), extract only the relevant calls via Grep. Patterns by domain:

| Domain | Grep pattern (engine-agnostic) |
|---|---|
| FSM state changes | `ChangeState\|SetState\|TransitionTo` |
| Animator string lookups | `Animator\.(SetBool\|SetFloat\|SetInteger\|SetTrigger\|GetBool)` |
| Input action bindings | `OnAction\|onPerformed\|InputAction\.` |
| Localization lookups | `Localize\|GetString\|TR\(` |
| Save/load fields | `Serialize\|FieldName\|JsonProperty` |

---

## Phase 3: Build the N-way matrix

For each *element* (state, parameter, key, field) found in *any* witness, fill a matrix:

| Element | Witness 1 (canonical) | Witness 2 | Witness 3 | ... | Severity |
|---|:---:|:---:|:---:|:---:|---|

Cell values: ✅ (present), ❌ (absent), ⚠️ (present with type/value mismatch).

### Severity classification rules

- 🚨 **High** — call site uses element that's missing from engine asset OR canonical spec. Causes silent runtime fail (engine ignores unknown name).
- 🚨 **High** — call site uses element with **type mismatch** (e.g. `SetBool("X")` but controller has `X` as Float). Engine silently coerces or ignores.
- ⚠️ **Medium** — element present in code + engine but missing from doc → spec drift, future-you forgets it exists.
- ⚠️ **Medium** — element in doc only → unimplemented promise (verify against backlog: maybe it's planned).
- ⚠️ **Medium** — element defined in engine asset but no call site references it → dead asset, possible cleanup.
- ℹ️ **Low** — minor cosmetic mismatches (label spelling, comment-vs-code).

---

## Phase 4: Type / value cross-check

For each element present in 2+ witnesses, also compare:

- **Type** — is it the same type everywhere? (Bool vs Int vs Float vs Trigger)
- **Default value** — does the code initial state match the doc default?
- **Range / enum membership** — does the code enum cover all states the doc lists?

A **type mismatch** is automatic 🚨 High even if the *name* matches across witnesses.

---

## Phase 5: Backlog cross-reference (optional)

If the user provides a backlog file path (Plan.md, ROADMAP.md, or similar), grep the backlog for each ⚠️ Medium finding. If a finding is already tracked as a planned item:

- Doc-only element + tracked in backlog → demote to ℹ️ (it's intentional, just not built yet).
- Dead asset + tracked for cleanup → demote to ℹ️.

This filters noise so the report only flags **unknown drift**.

---

## Phase 6: Produce the audit report

Output a markdown report with:

1. **Summary line** — `N elements scanned, H high / M medium / L low / OK count.`
2. **🚨 High section** — each row in matrix form, with file:line citations. These need fixing now.
3. **⚠️ Medium section** — same, ordered by inferred age (oldest first).
4. **ℹ️ Low section** — collapsed by default (`<details>` block).
5. **Action checklist** — bulleted "do this next" list. Concrete file edits if obvious; otherwise "investigate {witness X} {element Y}".
6. **Methodology footer** — list of witnesses scanned, grep patterns used, anything skipped (e.g. "Animator controller too large, parsed via Grep on `m_Name` only").

The report is *advisory* — never auto-edit. Hand the report to the user for triage.

---

## When NOT to use this skill

- When there's only one witness — it's not a SoT problem, it's a code review.
- When the witnesses are tightly coupled by tooling (e.g. enum + auto-generated bindings) — drift is structurally impossible there.
- For real-time runtime behaviour audits — use a logging hook or profiler, not a static scan.

---

## Generalises across game projects

The N-witness pattern applies wherever a logical specification has multiple physical homes:
**FSM** (doc + enum + animator + call sites), **input bindings** (action asset + reader + property surface + usage + doc), **save schemas** (schema doc + serializer + migration table + UI refs), **localization** (CSV + lookup calls + prefab refs), **audio mixer** (mixer asset + code lookups + doc), **shader uniforms**, **network messages**, **achievements** — all use the same audit pattern, only the witnesses differ.
