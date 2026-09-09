---
name: propagate-design-change
description: "When a GDD is revised, scans all ADRs and the traceability index to identify which architectural decisions are now potentially stale. Produces a change impact report and guides the user through resolution."
---

# Propagate Design Change

When a GDD changes, architectural decisions written against it may no longer be
valid. This skill finds every affected ADR, compares what the ADR assumed against
what the GDD now says, and records the resolution for each.

**Usage:** `$propagate-design-change design/gdd/combat-system.md`

---

## 1. Validate Argument

A GDD path argument is **required**. If missing, fail with:
> "Usage: `$propagate-design-change design/gdd/[system].md`
> Provide the path to the GDD that was changed."

Verify the file exists. If not, fail with:
> "[path] not found. Check the path and try again."

---

## 2. Read the Changed GDD

Read the current GDD in full.

---

## 3. Read the Previous Version

Run git to get the previous committed version:

```bash
git show HEAD:design/gdd/[filename].md
```

If the file has no git history (new file), report:
> "No previous version in git — this appears to be a new GDD, not a revision.
> Nothing to propagate."

If git returns the previous version, do a conceptual diff:
- Identify sections that changed (new rules, removed rules, modified formulas,
  changed acceptance criteria, changed tuning knobs)
- Identify sections that are unchanged
- Produce a change summary:

```
## Change Summary: [GDD filename]
Date of revision: [today]

Changed sections:
- [Section name]: [what changed — new rule, removed rule, formula modified, etc.]

Unchanged sections:
- [Section name]

Key changes affecting architecture:
- [Change 1 — likely to affect ADRs]
- [Change 2]
```

---

## 4. Load Architecture Inputs

Read all ADRs in `docs/architecture/`:
- For each ADR, read the full file
- Extract the "GDD Requirements Addressed" table
- Note which GDD documents and requirement IDs each ADR references

Read `docs/architecture/architecture-traceability.md` if it exists.

Report: "Loaded [N] ADRs. [M] reference [gdd filename]."

---

## 5. Impact Analysis

For each ADR that references the changed GDD:

Compare the ADR's "GDD Requirements Addressed" entries against the changed sections
of the GDD. For each referenced requirement:

1. **Locate the requirement** in the current GDD — does it still exist?
2. **Compare**: What did the GDD say when the ADR was written vs. what it says now?
3. **Assess the ADR decision**: Is the architectural decision still valid?

Classify each affected ADR as one of:

| Status | Meaning |
|--------|---------|
| ✅ **Still Valid** | The GDD change doesn't affect what this ADR decided |
| ⚠️ **Needs Review** | The GDD change may affect this ADR — human judgment needed |
| 🔴 **Likely Superseded** | The GDD change directly contradicts what this ADR assumed |

For each affected ADR, produce an impact entry:

```
### ADR-NNNN: [title]
Status: [Still Valid / Needs Review / Likely Superseded]

What the ADR assumed about this GDD:
  "[relevant quote from the ADR's GDD Requirements Addressed section]"

What the GDD now says:
  "[relevant quote from the current GDD]"

Assessment:
  [Explanation of whether the ADR decision is still valid, and why]

Recommended action:
  [Keep as-is | Review and update | Mark Superseded and write new ADR]
```

---

## 6. Present Impact Report

Assemble the full impact report before resolving anything. Format:

```
## Design Change Impact Report
GDD: [filename]
Date: [today]
Changes detected: [N sections changed]
ADRs referencing this GDD: [M]

### Not Affected
[ADRs referencing this GDD whose decisions remain valid]

### Needs Review ([count])
[ADRs that may need updating]

### Likely Superseded ([count])
[ADRs whose assumptions are now contradicted]
```

---

## 6b. Director Gate — Technical Impact Review

**Review mode check** — apply before spawning TD-CHANGE-IMPACT:
- `solo` → skip. Note: "TD-CHANGE-IMPACT skipped — Solo mode." Proceed to Phase 7.
- `lean` → skip. Note: "TD-CHANGE-IMPACT skipped — Lean mode." Proceed to Phase 7.
- `full` → spawn the named director as a separate reviewing subagent (read-only, final state only; `docs/director-gates.md`).

Spawn `technical-director` as a Codex subagent using gate **TD-CHANGE-IMPACT** (`../../docs/director-gates.md`).

Pass: the full Design Change Impact Report from Phase 6 (change summary, all affected ADRs with their Still Valid / Needs Review / Likely Superseded classifications, and recommended actions).

The technical-director reviews whether:
- The impact classifications are correct (no ADRs under-classified)
- The recommended actions are architecturally sound
- Any cascading effects on other ADRs or systems were missed

Apply the verdict:
- **APPROVE** → proceed to Phase 7 resolution workflow
- **CONCERNS** → revise the assessment for each flagged ADR where the flag holds; otherwise accept and carry the concern into the report. Name each choice in the report.
- **REJECT** → do not proceed to resolution; re-analyze the impact before continuing

---

## 7. Resolution Workflow

Resolve each ADR marked "Needs Review" or "Likely Superseded" by its status. If you
deviate, name the reason in the report.

- **Likely Superseded** → set the ADR's Status field to
  `Superseded by ADR-[next number] (pending — see change-impact-[date]-[system].md)`.
  The decision text stays untouched; the replacement ADR is written later with
  `$architecture-decision`.
- **Needs Review** → append a `Needs Review ([date]): [what to check]` line under the
  Status field. Do not rewrite the decision — reopening a confirmed ADR is the user's
  call (`../../rules/decision-lifecycle.md` § 4).
- **Still Valid** → no edit.

Report every ADR touched with its revert command (`git checkout -- <path>`).

---

## 8. Update Traceability Index

If `docs/architecture/architecture-traceability.md` exists:
- Add the changed GDD requirements to the "Superseded Requirements" table:

```markdown
## Superseded Requirements
| Date | GDD | Requirement | Changed To | ADRs Affected | Resolution |
|------|-----|-------------|------------|---------------|------------|
| [date] | [gdd] | [old requirement text] | [new requirement text] | ADR-NNNN | [Superseded/Updated/Valid] |
```

Write the rows. Report the path and the revert command.

---

## 9. Output Change Impact Document

Write the change impact report to `docs/architecture/change-impact-[date]-[system-slug].md`.
Report the path and the revert command (`git checkout -- <path>`).

The document contains:
- The change summary from step 3
- The full impact analysis from step 5
- Resolution decisions made in step 7
- List of ADRs that need to be written or updated

Verdict: **COMPLETE** — change impact report saved.

---

## 10. Follow-Up Actions

Based on the resolution decisions, suggest:

- **ADRs marked Superseded**: "Run `$architecture-decision [title]` to write the
  replacement ADR. Then re-run `$propagate-design-change` to verify coverage."
- **ADRs to update in place**: List the specific fields to update in each ADR
- **If many ADRs affected**: "Run `$architecture-review` after all ADRs are updated
  to verify the full traceability matrix is still coherent."

---

## Collaborative Protocol

1. **Read silently** — compute the full impact before resolving anything
2. **Resolve per-ADR** — each affected ADR gets its own status-driven resolution (§ 7), named in the report
3. **Write and report** — every file touched is listed with its revert command
4. **Non-destructive** — never delete or rewrite ADR decision text; only add status and "Needs Review" notes
