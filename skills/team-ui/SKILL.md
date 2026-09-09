---
name: team-ui
description: "Orchestrate the UI team through the full UX pipeline: from UX spec authoring through visual design, implementation, review, and polish. Integrates with $ux-design, $ux-review, and studio UX templates."
---
When this skill is invoked, orchestrate the UI team through a structured pipeline.

**Decision Points:** Proceed through phases autonomously. Record each phase's
decision and the alternatives rejected in the final report; stop only on K1/K2
or a gate exit 2 (`rules/autonomy-contract.md`).

## Team Composition
- **ux-designer** — User flows, wireframes, accessibility, input handling
- **ui-programmer** — UI framework, screens, widgets, data binding, implementation
- **art-director** — Visual style, layout polish, consistency with art bible
- **engine UI specialist** — Validates UI implementation patterns against engine-specific best practices (read from `.codex/studio/technical-preferences.md` Engine Specialists → UI Specialist)
- **accessibility-specialist** — Audits accessibility compliance at Phase 4

**Templates used by this pipeline:**
- `ux-spec.md` — Standard screen/flow UX specification
- `hud-design.md` — HUD-specific UX specification
- `interaction-pattern-library.md` — Reusable interaction patterns
- `accessibility-requirements.md` — Committed accessibility tier and requirements

## How to Delegate

Use the Codex subagent mechanism to spawn each team member as a subagent:
- `subagent_type: ux-designer` — User flows, wireframes, accessibility, input handling
- `subagent_type: ui-programmer` — UI framework, screens, widgets, data binding
- `subagent_type: art-director` — Visual style, layout polish, art bible consistency
- `subagent_type: [UI engine specialist]` — Engine-specific UI pattern validation (e.g., unity-ui-specialist, ue-umg-specialist, godot-specialist)
- `subagent_type: accessibility-specialist` — Accessibility compliance audit

Always provide full context in each agent's prompt (feature requirements, existing UI patterns, platform targets). Launch independent agents in parallel where the pipeline allows it (e.g., Phase 4 review agents can run simultaneously).

## Pipeline

### Phase 1a: Context Gathering

Before designing anything, read and synthesize:
- `design/gdd/game-concept.md` — platform targets and intended audience
- `design/player-journey.md` — player's state and context when they reach this screen
- All GDD UI Requirements sections relevant to this feature
- `design/ux/interaction-patterns.md` — existing patterns to reuse (not reinvent)
- `design/accessibility-requirements.md` — committed accessibility tier (e.g., Basic, Enhanced, Full)

**If `design/ux/interaction-patterns.md` does not exist**, surface the gap immediately:
> "interaction-patterns.md does not exist — no existing patterns to reuse."

Take (a) unless the argument scopes the run to a single small screen; then (b). If you deviate, name the reason in the report.
- (a) Run `$ux-design patterns` first to establish the pattern library, then continue
- (b) Proceed without the pattern library — instruct ui-programmer in Phase 3 to treat all patterns as new and add each to a new `design/ux/interaction-patterns.md` when implementation is complete

Do NOT invent or assume patterns from the feature name or GDD alone. Note the pattern library status (created / absent / updated) in the final summary report.

Summarize the context in a brief for the ux-designer: what the player is doing, what they need, what constraints apply, and which existing patterns are relevant.

### Phase 1b: UX Spec Authoring

Invoke `$ux-design [feature name]` skill OR delegate directly to ux-designer to produce `design/ux/[feature-name].md` following the `ux-spec.md` template.

If designing the HUD, use the `hud-design.md` template instead of `ux-spec.md`.

> **Notes on special cases:**
> - For HUD design specifically, invoke `$ux-design` with `argument: hud` (e.g., `$ux-design hud`).
> - For the interaction pattern library, run `$ux-design patterns` once at project start and update it whenever new patterns are introduced during later phases.

Output: `design/ux/[feature-name].md` with all required spec sections filled.

### Phase 1c: UX Review

After the spec is complete, invoke `$ux-review design/ux/[feature-name].md`.

**Gate**: The `$ux-review` verdict decides. On NEEDS REVISION, the ux-designer addresses the flagged issues and the review is re-run within the `$self-loop` limits (`rules/self-loop.md`). If it still fails, stop: Verdict: **BLOCKED** — ux-review NEEDS REVISION; list the specific concerns. Accepting that risk and proceeding is a K1 decision for the user.

### Phase 2: Visual Design

Delegate to **art-director**:
- Review the full UX spec (flows, wireframes, interaction patterns, accessibility notes) — not just the wireframe images
- Apply visual treatment from the art bible: colors, typography, spacing, animation style
- Check that visual design preserves accessibility compliance: verify color contrast ratios, and confirm color is never the only indicator of state (shape, text, or icon must reinforce it)
- Specify all asset requirements needed from the art pipeline: icons at specified sizes, background textures, fonts, decorative elements — with precise dimensions and format requirements
- Ensure consistency with existing implemented UI screens
- Output: visual design spec with style notes and asset manifest

### Phase 3: Implementation

Before implementation begins, spawn the **engine UI specialist** (from `.codex/studio/technical-preferences.md` Engine Specialists → UI Specialist) to review the UX spec and visual design spec for engine-specific implementation guidance:
- Which engine UI framework should be used for this screen? (e.g., UI Toolkit vs UGUI in Unity, Control nodes vs CanvasLayer in Godot, UMG vs CommonUI in Unreal)
- Any engine-specific gotchas for the proposed layout or interaction patterns?
- Recommended widget/node structure for the engine?
- Output: engine UI implementation notes to hand off to ui-programmer before they begin

If no engine is configured, skip this step.

Delegate to **ui-programmer**:
- Implement the UI following the UX spec and visual design spec
- **Use patterns from `design/ux/interaction-patterns.md`** — do not reinvent patterns that are already specified. If a pattern almost fits but needs modification, note the deviation and flag it for ux-designer review.
- **UI NEVER owns or modifies game state** — display only; emit events for all player actions
- All text through the localization system — no hardcoded player-facing strings
- Support both input methods (keyboard/mouse AND gamepad)
- Implement accessibility features per the committed tier in `design/accessibility-requirements.md`
- Wire up data binding to game state
- **If any new interaction pattern is created during implementation** (i.e., something not already in the pattern library), add it to `design/ux/interaction-patterns.md` before marking implementation complete
- Output: implemented UI feature

### Phase 4: Review (parallel)

Delegate in parallel:
- **ux-designer**: Verify implementation matches wireframes and interaction spec. Test keyboard-only and gamepad-only navigation. Check accessibility features function correctly.
- **art-director**: Verify visual consistency with art bible. Check at minimum and maximum supported resolutions.
- **accessibility-specialist**: Verify compliance against the committed accessibility tier documented in `design/accessibility-requirements.md`. Flag any violations as blockers.

All three review streams must report before proceeding to Phase 5.

### Phase 5: Polish

- Address all review feedback
- Verify animations are skippable and respect the player's motion reduction preferences
- Confirm UI sounds trigger through the audio event system (no direct audio calls)
- Test at all supported resolutions and aspect ratios
- **Verify `design/ux/interaction-patterns.md` is up to date** — if any new patterns were introduced during this feature's implementation, confirm they have been added to the library
- **Confirm all HUD elements respect the visual budget** defined in `design/ux/hud.md` (element count, screen region allocations, maximum opacity values)

## Quick Reference — When to Use Which Skill

- `$ux-design` — Author a new UX spec for a screen, flow, or HUD from scratch
- `$ux-review` — Validate a completed UX spec before implementation
- `$team-ui [feature]` — Full pipeline from concept through polish (calls `$ux-design` and `$ux-review` internally)
- `$quick-design` — Small UI changes that don't need a full new UX spec

## Error Recovery Protocol

If any spawned agent (as a Codex subagent) returns BLOCKED, errors, or cannot complete:

1. **Record it**: "[AgentName]: BLOCKED — [reason]" and the phase it interrupted, in the final report
2. **Choose the narrowest recovery yourself and report it**: retry with narrower scope, or skip the agent and note the gap
3. **BLOCKED only when the missing output is required by a later phase and cannot be reproduced** (K1/K2). Name what is needed to resume
4. **Always produce a partial report** — output whatever was completed. Never discard work because one agent blocked.

Common blockers:
- Input file missing (story not found, GDD absent) → redirect to the skill that creates it
- ADR status is Proposed → do not implement; run `$architecture-decision` first
- Scope too large → split into two stories via `$create-stories`
- Conflicting instructions between ADR and story → surface the conflict, do not guess

## File Write Protocol

All file writes (UX specs, interaction pattern library updates, implementation
files) are delegated to sub-agents and sub-skills (`$ux-design`, `ui-
programmer`). This orchestrator does not write files directly. Each sub-agent
writes only within its owned paths (`rules/subagent-collaboration.md` § 3) and
returns the paths written; list every path with its revert command (`git
checkout -- <path>`) in the final report.

## Output

A summary report covering: UX spec status, UX review verdict, visual design status, implementation status, accessibility compliance, input method support, interaction pattern library update status, and any outstanding issues.

Verdict: **COMPLETE** — UI feature delivered through full pipeline (UX spec → visual → implementation → review → polish).
Verdict: **BLOCKED** — pipeline halted; surface the blocker and its phase before stopping.

## Next Steps

- Run `$ux-review` on the final spec if not yet approved.
- Run `$code-review` on the UI implementation before closing stories.
- Run `$team-polish` if visual or audio polish pass is needed.
