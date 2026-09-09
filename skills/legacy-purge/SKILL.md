---
name: legacy-purge
description: "Audit a codebase for legacy residue after a pivot, deprecation, or major migration. Produces a categorized table of suspect files / patterns / strings — never auto-deletes. Use when user says 'purge v1', 'clean up old API', 'find legacy residue', 'audit migration leftovers'."
---

## Purpose

After a major pivot — a version migration, a platform change, an API deprecation, an architectural rewrite — code, docs, assets, and config files inherit residue from the *old* world. Some residue is **intentionally retained** (recyclable code, archived docs); some is **dead weight** that creates confusion, breaks builds intermittently, or leaks deprecated assumptions into new code.

This skill produces a **categorized audit report** of suspect residue. It never auto-deletes — every finding is human-reviewed.

Read-only: writes nothing — the report is returned in the conversation; no file is edited, deleted, or staged.

Examples of pivot/migration scenarios:
- **Genre pivot** — mobile vertical → PC horizontal
- **API deprecation** — legacy input system → new input system
- **Platform change** — mobile-only → multi-platform (must remove platform-specific dependencies)
- **Architecture rewrite** — monolith → modular, ECS adoption, server-authoritative refactor
- **Library swap** — one rendering pipeline → another, one networking lib → another

---

## Phase 1: Identify the migration

From `the invocation arguments`:
- `$1` = from-context (e.g. `v1`, `legacy-input`, `mobile-only`, `monolith`)
- `$2` = to-context (e.g. `v2`, `input-system`, `cross-platform`, `modular`)
- `$3` (optional) = scope glob (e.g. `src/**`, `Assets/02.Scripts/**`, `docs/**`)

If args missing, ask the user:

> What pivot are we auditing?
> - From: <e.g. mobile-vertical-Forward-Rush>
> - To: <e.g. PC-horizontal-cover-shooter>
> - Scope: <which directories — defaults to all source / docs>

Also ask for **policy documents** that define what stays vs goes (e.g. "v1 archived doc", "deprecation memo", "migration plan"). These determine residue severity.

---

## Phase 2: Build a category checklist

For the named migration, brainstorm 4-8 *residue categories*. Each category = one type of legacy footprint.

### Category template

| Category | Severity tier | Detection method |
|---|---|---|
| Deprecated API calls | 🚨 immediate removal | grep for API symbols |
| Platform-specific dependencies (when going cross-platform) | 🚨 immediate removal | grep for platform classes / namespaces |
| Old genre/mode-specific logic | ⚠️ context review | grep for genre-specific keywords / variable names |
| Old screen/input-mode constants | ⚠️ context review | grep for orientation / aspect ratio / input type literals |
| Migration-flag stubs | ⚠️ context review | grep for `// TODO migrate`, `#if LEGACY`, deprecated feature flags |
| Old asset references | ⚠️ context review | grep for old asset paths in scenes / prefabs / scripts |
| Stale doc sections | ℹ️ doc cleanup | grep in `docs/`, `Documents/` for old version mentions |
| Archive directories | ℹ️ already isolated | check for `_archive/`, `legacy/`, `v1/` paths |

Use this as a starter, then **customize categories per migration**. Ask the user to confirm or extend the category list before scanning.

---

## Phase 3: Run categorized greps in parallel

For each confirmed category, run a `Grep` with:
- Pattern matching old-context symbols
- Glob restricting to the scope
- Output mode `count` for quick prevalence, then `files_with_matches` for review

If a category needs subtler detection (variable names, comment text, file naming patterns), use `Glob` for filenames + `Grep` for content separately, then merge.

**Parallelize all category scans** — one tool call message with N greps.

---

## Phase 4: Cross-reference policy docs

For each finding, check if the policy doc (from Phase 1) **explicitly classifies** it:
- "Discard" / "❌ remove" → keep at original severity
- "Recycle" / "♻️ adapt" → demote ⚠️ → ℹ️ (intentional retention)
- "Archive" → demote to ℹ️ (already known)
- Not mentioned → keep severity, flag as "policy gap" in report

This filters out "I already decided to keep this" findings, leaving only **unknown drift**.

---

## Phase 5: Produce the residue report

Output a markdown table per category:

```
## Cat A: Deprecated API calls 🚨

| File | Line | Symbol | Policy | Action |
|---|---|---|---|---|
| src/Foo.cs | 42 | LegacyAPI.GetX() | "❌ remove" | Replace with NewAPI.GetX |
| src/Bar.cs | 13 | LegacyAPI.SetY() | not in policy | Investigate — policy gap |
```

Include:
1. **Summary line per category** — `N findings, S severity tier`
2. **Total counts by tier** — `🚨 X / ⚠️ Y / ℹ️ Z`
3. **Action checklist** — bulleted "do this next" by tier
4. **Policy gaps** — findings not classified in any policy doc; recommend adding to policy
5. **What was NOT scanned** — categories you considered but skipped, with reason

The report is **advisory only** — never auto-edit, never delete, never even stage changes for the user. They review file-by-file.

---

## Phase 6: Suggest follow-up

If 🚨 findings exist, suggest:
- "Run a fix-up commit per category — keeps history readable"
- "Add a CI lint to prevent regression of fixed patterns"

If ⚠️ findings exist:
- "Schedule a review session before the next sprint to triage"

If only ℹ️ findings:
- "Update policy doc to explicitly classify these" — closes policy gaps

---

## When NOT to use this skill

- Before the migration is **declared done** — purging mid-migration deletes work-in-progress.
- For simple one-symbol rename — just use IDE refactor or `Grep`+`Edit`.
- For *currently-supported legacy paths* (backwards-compat code) — those are intentional residue, not drift.

---

## Generalises across game projects

The same audit pattern applies to: engine version upgrades (Unity 2022 → 6, Godot 3 → 4, Unreal 4 → 5), rendering pipeline swaps (built-in → URP, deferred → forward), networking refactors (P2P → server-auth, custom → relay), genre pivots (single-player → live-service, premium → F2P), platform additions or removals. Define the 4-8 categories specific to your migration; the workflow is identical.
