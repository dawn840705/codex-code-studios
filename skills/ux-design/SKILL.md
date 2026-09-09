---
name: ux-design
description: "Guided, section-by-section UX spec authoring for a screen, flow, or HUD. Reads game concept, player journey, and relevant GDDs to provide context-aware design guidance. Produces ux-spec.md (per screen/flow) or hud-design.md using the studio templates."
---

> **Track check — this skill is game-framed.** Resolve `production/track.txt` (or the
> session's `PROJECT_TYPE` line) before Phase 0.
>
> - **`game`** — run as written.
> - **`product`** (web / mobile / service) — substitute as you read: player becomes user,
>   game becomes product, GDD becomes PRD (`design/gdd/` → `product/prd/`), engine becomes
>   the stack pinned in `.codex/studio/technical-preferences.md`. Read the feature's PRD in place of a GDD. Input is pointer, touch and keyboard — skip the controller-mapping and HUD sections entirely. Output still lands in `design/ux/`.
> - **Unresolved** — ask which track this is before doing anything. A greenfield project
>   has no signal either way; do not infer one from the repository contents.

When this skill is invoked:

## 1. Parse Arguments & Determine Mode

Three authoring modes exist based on the argument:

| Argument | Mode | Output file |
|----------|------|-------------|
| `hud` | HUD design | `design/ux/hud.md` |
| `patterns` | Interaction pattern library | `design/ux/interaction-patterns.md` |
| Any other value (e.g., `main-menu`, `inventory`) | UX spec for a screen or flow | `design/ux/[argument].md` |
| No argument | Derive from project state | (see below) |

**If no argument is provided**, derive the target and report it:
1. `design/ux/interaction-patterns.md` missing → `patterns`
2. Else `design/ux/hud.md` missing and the game has a HUD → `hud`
3. Else the first screen named in a GDD UI Requirements section with no file in `design/ux/`

If none of the three resolves (K2): "Usage: `$ux-design <screen|hud|patterns>`." Verdict: **BLOCKED** — no design target.

Normalize a screen name to kebab-case for the filename (e.g., "Main Menu" becomes `main-menu`).

---

## 2. Gather Context (Read Phase)

Read all relevant context **before** drafting anything. The skill's value
comes from arriving informed.

### 2a: Required Reads

- **Game concept**: Read `design/gdd/game-concept.md` — if missing, warn:
  > "No game concept found. Run `$brainstorm` first to establish the game's
  > foundation before designing UX."
  > Continue; mark every assumption that would have come from it `[확인 필요]`.

### 2b: Player Journey

Read `design/player-journey.md` if it exists. For each relevant section, extract:
- Which journey phase(s) does this screen appear in?
- What is the player's emotional state on arrival at this screen?
- What player need is this screen serving in the journey?
- What critical moments (from the journey map) does this screen deliver?

If the player journey file does not exist, note the gap and proceed:
> "No player journey map found at `design/player-journey.md`. Designing without it
> means we'll be making assumptions about player context. Consider running a player
> journey session after this spec is drafted."

### 2c: GDD UI Requirements

Glob `design/gdd/*.md` and grep for `UI Requirements` sections. Read any GDD whose
UI Requirements section references this screen by name or category.

These GDD UI Requirements are the **requirements input** to this spec. Collect them
as a list of constraints the spec must satisfy.

If designing the HUD, read ALL GDD UI Requirements sections — the HUD aggregates
requirements from every system.

### 2d: Existing UX Specs

Glob `design/ux/*.md` and note which screens already have specs. For screens that
will link to or from the current screen, read their navigation/flow sections to
find the entry and exit points this spec must match.

### 2e: Interaction Pattern Library

If `design/ux/interaction-patterns.md` exists, read the pattern catalog index
(the list of pattern names and their one-line descriptions). Do not read full
pattern details — just the catalog. This tells you which patterns already exist
so you can reference them rather than reinvent them.

### 2f: Art Bible

Check for `design/art/art-bible.md`. If found, read the visual direction
section. UX layout must align with the aesthetic commitments already made.

### 2g: Accessibility Requirements

Check for `design/accessibility-requirements.md`. If found, read it. The spec
must satisfy the accessibility tier committed to there.

### 2h: Input Method (from Project Config)

Read `.codex/studio/technical-preferences.md` and extract the `## Input & Platform`
section. Store these values for use throughout the skill — they drive the
Interaction Map and inform accessibility requirements:

- **Input Methods** — e.g., Keyboard/Mouse, Gamepad, Touch, Mixed
- **Primary Input** — the dominant input for this game
- **Gamepad Support** — Full / Partial / None
- **Touch Support** — Full / Partial / None
- **Target Platforms** — for safe zone and aspect ratio decisions

If the section is unconfigured (`[TO BE CONFIGURED]`), derive the input methods
once from the platform targets in `design/gdd/game-concept.md`. If that is silent
too, take "Both (PC + Console)" and mark it `[확인 필요]` in the report, with
"Run `$setup-engine` to pin this permanently."

Store the result for the rest of this session. Do **not** re-derive it per
section or per screen.

### 2i: Present Context Summary

Before any design work, present a brief summary to the user:

> **Designing: [Screen/Flow Name]**
> - Mode: [UX Spec / HUD Design / Pattern Library]
> - Journey phase(s): [from player-journey.md, or "unknown — no journey map"]
> - GDD requirements feeding this spec: [count and names, or "none found"]
> - Related screens already specced: [list, or "none yet"]
> - Known patterns available: [count, or "no pattern library yet"]
> - Accessibility tier: [from requirements doc, or "not yet defined"]
> - Input methods: [from technical-preferences.md, or "derived above"]

Then proceed.

---

## 2b. Retrofit Mode Detection

Before creating a skeleton, check if the target output file already exists.

Glob `design/ux/[filename].md` (where `[filename]` is the resolved output path from Phase 1).

**If the file exists — retrofit mode:**
- Read the file in full
- For each expected section, check whether the body has real content (more than a `[To be designed]` placeholder) or is empty/placeholder
- Present a section status summary to the user:

> "Found existing UX spec at `design/ux/[filename].md`. Here's what's already done:
>
> | Section | Status |
> |---------|--------|
> | Overview & Context | [Complete / Empty / Placeholder] |
> | Player Journey Integration | ... |
> | Screen Layout & Information Architecture | ... |
> | Interaction Model | ... |
> | Feedback & State Communication | ... |
> | Accessibility | ... |
> | Edge Cases & Error States | ... |
> | Open Questions | ... |
>
> I'll work on the [N] incomplete sections only — existing content will not be overwritten."

- Skip Section 3 (skeleton creation) — the file already exists
- In Phase 4 (Section Authoring), only work on sections with Status: Empty or Placeholder
- Use `Edit` to fill placeholders in-place rather than creating a new skeleton

**If the file does not exist — fresh authoring mode:**
Proceed to Phase 3 (Create File Skeleton) as normal.

---

## 3. Create File Skeleton

**Immediately** create the output file at `design/ux/[filename].md` with empty
section headers. This ensures incremental writes have a target and work survives
interruptions. Report the path and the revert command (`git checkout -- <path>`).

---

### Skeleton for UX Spec (screen or flow)

```markdown
# UX Spec: [Screen/Flow Name]

> **Status**: In Design
> **Author**: [user + ux-designer]
> **Last Updated**: [today's date]
> **Journey Phase(s)**: [from context]
> **Template**: UX Spec

---

## Purpose & Player Need

[To be designed]

---

## Player Context on Arrival

[To be designed]

---

## Navigation Position

[To be designed]

---

## Entry & Exit Points

[To be designed]

---

## Layout Specification

### Information Hierarchy

[To be designed]

### Layout Zones

[To be designed]

### Component Inventory

[To be designed]

### ASCII Wireframe

[To be designed]

---

## States & Variants

[To be designed]

---

## Interaction Map

[To be designed]

---

## Events Fired

[To be designed]

---

## Transitions & Animations

[To be designed]

---

## Data Requirements

[To be designed]

---

## Accessibility

[To be designed]

---

## Localization Considerations

[To be designed]

---

## Acceptance Criteria

[To be designed]

---

## Open Questions

[To be designed]
```

---

### Skeleton for HUD Design

```markdown
# HUD Design

> **Status**: In Design
> **Author**: [user + ux-designer]
> **Last Updated**: [today's date]
> **Template**: HUD Design

---

## HUD Philosophy

[To be designed]

---

## Information Architecture

### Full Information Inventory

[To be designed]

### Categorization

[To be designed]

---

## Layout Zones

[To be designed]

---

## HUD Elements

[To be designed]

---

## Dynamic Behaviors

[To be designed]

---

## Platform & Input Variants

[To be designed]

---

## Accessibility

[To be designed]

---

## Open Questions

[To be designed]
```

---

### Skeleton for Interaction Pattern Library

```markdown
# Interaction Pattern Library

> **Status**: In Design
> **Author**: [user + ux-designer]
> **Last Updated**: [today's date]
> **Template**: Interaction Pattern Library

---

## Overview

[To be designed]

---

## Pattern Catalog

[To be designed]

---

## Patterns

[Individual pattern entries added here as they are defined]

---

## Gaps & Patterns Needed

[To be designed]

---

## Open Questions

[To be designed]
```

---

After writing the skeleton, update `production/session-state/active.md` with:
- Task: Designing [screen/flow name] UX spec
- Current section: Starting (skeleton created)
- File: design/ux/[filename].md

---

## 4. Section-by-Section Authoring

Walk through each section in order. For **each section**, follow this cycle:

```
Context  ->  Derive  ->  Decide  ->  Draft  ->  Write  ->  Record
```

1. **Context**: State what this section needs to contain and surface any relevant
   constraints from context gathered in Phase 2.
2. **Derive**: Answer the section's questions from the GDD, the player journey,
   existing specs, and the pattern library. Where the sources are silent, take the
   most conservative reading and mark it `[확인 필요]`.
3. **Decide**: Where design choices exist, list 2-4 approaches with pros/cons.
   Take the one consistent with existing specs and the art bible; when that does
   not separate them, the platform default. Record the rejected ones and the reason.
4. **Draft**: Write the section content. Flag provisional assumptions explicitly.
5. **Write**: Use `Edit` to replace the `[To be designed]` placeholder with the
   content.
6. **Record**: Add the section's decisions and `[확인 필요]` items to the running
   report. The whole document gets one review pass at handoff (Phase 5).

After writing each section, update `production/session-state/active.md`.

---

### Section Guidance: UX Spec Mode

#### Section A: Purpose & Player Need

This section is the foundation. Every other decision flows from it.

**Questions this section answers**:
- "What player goal does this screen serve? What is the player trying to DO here?"
- "What would go wrong if this screen didn't exist or was hard to use?"
- "Complete this sentence: 'The player arrives at this screen wanting to ___.' "

Cross-reference the player journey context gathered in Phase 2. The stated purpose
must align with the journey phase and emotional state.

---

#### Section B: Player Context on Arrival

**Questions this section answers**:
- "When in the game does a player first encounter this screen?"
- "What were they just doing immediately before reaching this screen?"
- "What emotional state should the design assume? (calm, stressed, curious, time-pressured)"
- "Do players arrive at this screen voluntarily, or are they sent here by the game?"

Offer to map this against the journey phases if the player journey doc exists.

---

#### Section B2: Navigation Position

Where does this screen sit in the game's navigation hierarchy? This is a one-paragraph orientation map — not a full flow diagram.

**Questions this section answers**:
- "Is this screen accessed from the main menu, from pause, from within gameplay, or from another screen?"
- "Is it a top-level destination (always reachable) or a context-dependent one (only accessible in certain states)?"
- "Can the player reach this screen from more than one place in the game?"

Present as: "This screen lives at: [root] → [parent] → [this screen]" plus any alternate entry paths.

---

#### Section B3: Entry & Exit Points

Map every way the player can arrive at and leave this screen.

**Questions this section answers**:
- "What are all the ways a player can reach this screen?" (List each trigger: button press, game event, redirect from another screen, etc.)
- "What can the player do to exit? What happens when they do?" (Back button, confirm action, timeout, game event)
- "Are there any exits that are one-way — where the player cannot return to this screen without starting over?"

Present as two tables:

| Entry Source | Trigger | Player carries this context |
|---|---|---|
| [screen/event] | [how] | [state/data they arrive with] |

| Exit Destination | Trigger | Notes |
|---|---|---|
| [screen/event] | [how] | [any irreversible state changes] |

---

#### Section C: Layout Specification

This is the largest and most interactive section. Work through it in sub-sections:

**Sub-section 1 — Information Hierarchy** (establish this before any layout):
- List every piece of information this screen must communicate, from the GDD UI
  Requirements and the player journey.
- Rank the items: what a player needs to see first, what second, what can be
  discovered rather than immediately visible. Rank by the decision the journey
  phase asks the player to make.
- Record the resulting hierarchy before moving to zones.

**Sub-section 2 — Layout Zones**:
- Based on the information hierarchy, propose rough screen zones (header, content
  area, action bar, sidebar, etc.).
- List 2-3 zone arrangements with rationale for each. Reference platform and
  input context gathered from game concept.
- Take the arrangement that matches the existing specs' conventions; with no
  existing specs, the platform default. Record the rejected ones.

**Sub-section 3 — Component Inventory**:
- For each zone, list the UI components it contains. For each component, note:
  - Component type (button, list, card, stat display, input field, etc.)
  - Content it displays
  - Whether it is interactive
  - If it uses an existing pattern from the library (reference by pattern name)
  - If it introduces a new pattern (flag for later addition to the library)

**Sub-section 4 — ASCII Wireframe**:
- Generate an ASCII wireframe from the zone layout and component list and
  include it in the spec. Removing it in favour of an attached file is one edit.

---

#### Section D: States & Variants

Think beyond the happy path.

**Questions this section answers** (work through these one at a time):
- "What does this screen look like the very first time a player sees it, when there
  is no data yet? (empty state)"
- "What happens when something goes wrong — an error, a failed action, a missing
  resource? (error state)"
- "Is there ever a loading wait on this screen? If so, what does it show? (loading state)"
- "Are there any player progression states that change what this screen shows? For
  example, locked content, premium content, or tutorial-mode overlays?"
- "Does this screen behave differently on any supported platform? (platform variant)"

Record the collected states as a table:

| State / Variant | Trigger | What Changes |
|-----------------|---------|--------------|
| Default | Normal load | — |
| Empty | No data available | [content area description] |
| [etc.] | [trigger] | [changes] |

---

#### Section E: Interaction Map

For each interactive component identified in the Layout Specification, define:
- The action (tap, click, press, hold, scroll, drag)
- The platform input(s) that trigger it (mouse click, gamepad A, keyboard Enter)
- The immediate feedback (visual, audio, haptic)
- The outcome (navigation target, state change, data write)

Use the input methods loaded from `technical-preferences.md` in Phase 2h — do
not ask the user again. State them upfront: "Mapping interactions for:
[Input Methods from tech-prefs]. Covering [Gamepad Support] gamepad support."

Work through components one at a time.
For navigation actions (going to another screen), verify the target matches
an existing UX spec or note it as a spec dependency.

---

#### Section E2: Events Fired

For every player action in the Interaction Map, document the corresponding event the game or analytics system should fire — or explicitly note "no event" if none applies.

**Questions this section answers**:
- "For each action, should the game fire an analytics event, trigger a game-state change, or both?"
- "Are there any actions that should NOT fire an event — and is that a deliberate choice?"

Present as a table alongside the Interaction Map:

| Player Action | Event Fired | Payload / Data |
|---|---|---|
| [action] | [EventName] or none | [data passed with event] |

Flag any action that modifies persistent game state (save data, progress, economy) — these need explicit attention from the architecture team.

---

#### Section E3: Transitions & Animations

Specify how the screen enters and exits, and how it responds to state changes.

**Questions this section answers**:
- "How does this screen appear? (fade in, slide from right, instant pop, scale from button)"
- "How does it dismiss? (fade out, slide back, cut)"
- "Are there any in-screen state transitions that need animation? (loading spinner, success state, error flash)"
- "Is there any animation that could cause motion sickness — and does the product have a reduced-motion option?"

Minimum required:
- Screen enter transition
- Screen exit transition
- At least one state-change animation if the screen has multiple states

**Product track — specify the physics, not just the duration.** A fixed duration has no
idea where an interruption left it, so a second click or a fast scroll makes it snap. Say
which transitions are interruptible and give those a spring (stiffness / damping) rather
than a duration-plus-easing pair. `../../docs/motion-design-sources.md` has the reference
gallery and the briefing format — read it, do not copy its code (licence unverified).

---

#### Section F: Data Requirements

Cross-reference the GDD UI Requirements sections gathered in Phase 2.

For each piece of information the screen displays, answer:
- "Where does this data come from? Which system owns it?"
- "Does this screen need to write data back, or is it read-only?"
- "Is any of this data time-sensitive or real-time? (health bars, cooldown timers)"

Flag any case where the UI would need to own or manage game state as an architectural
concern. UX specs define what the UI needs; they do not dictate how the data is
delivered. That is an architecture decision.

Present the data requirements as a table:

| Data | Source System | Read / Write | Notes |
|------|--------------|--------------|-------|
| [item] | [system] | Read | — |
| [item] | [system] | Write | [concern if any] |

---

#### Section G: Accessibility

Cross-reference `design/accessibility-requirements.md` if it exists.

Walk through the ux-designer agent's standard checklist for this screen:
- Keyboard-only navigation path through all interactive elements
- Gamepad navigation order (if applicable)
- Text contrast and minimum readable font sizes
- Color-independent communication (no information conveyed by color alone)
- Screen reader considerations for any non-text elements
- Any motion or animation that needs a reduced-motion alternative

Read the committed tier from `design/accessibility-requirements.md`. If the file
is absent, write the section against the Basic tier and add an Open Question
marked `[확인 필요]`: "Accessibility tier not yet committed." Never skip the section.

---

#### Section H: Localization Considerations

Document constraints that affect how this screen behaves when text is translated.

**Questions this section answers**:
- "Which text elements on this screen are the longest? What is the maximum character count that fits the layout?"
- "Are there any elements where text length is layout-critical — e.g., a button label that must stay on one line?"
- "Are there any elements that display numbers, dates, or currencies that need locale-specific formatting?"

Note: aim to flag any element where a 40% text expansion (common in translations from English to German or French) would break the layout. Mark those as HIGH PRIORITY for the localization engineer.

---

#### Section I: Acceptance Criteria

Write at least 5 specific, testable criteria that a QA tester can verify without reading any other design document. These become the pass/fail conditions for `$story-done`.

**Format**: Use checkboxes. Each criterion must be verifiable by a human tester:

```
- [ ] Screen opens within [X]ms from [trigger]
- [ ] [Element] displays correctly at [minimum] and [maximum] values
- [ ] [Navigation action] correctly routes to [destination screen]
- [ ] Error state appears when [condition] and shows [specific message or icon]
- [ ] Keyboard/gamepad navigation reaches all interactive elements in logical order
- [ ] [Accessibility requirement] is met — e.g., "all interactive elements have focus indicators"
```

**Minimum required**:
- 1 performance criterion (load/open time)
- 1 navigation criterion (at least one entry or exit path verified)
- 1 error/empty state criterion
- 1 accessibility criterion (per committed tier)
- 1 criterion specific to this screen's core purpose

Check each criterion the way `$qa-plan` will: a tester must be able to verify it without the designer present. Rewrite any that fail that test.

---

### Section Guidance: HUD Design Mode

HUD design follows a different order from UX spec mode. Begin with philosophy;
do not touch layout until the information architecture is complete.

#### Section A: HUD Philosophy

State the game's relationship with on-screen information in 1-2 sentences,
derived from the pillars and tone in `design/gdd/game-concept.md`; cite the
pillar. This is creative direction, so mark it `[확인 필요]`.

Framing examples:
- "Nearly HUD-free — atmosphere requires unobstructed immersion (e.g., Hollow Knight, Firewatch)"
- "Minimal but present — only critical information visible, everything else contextual (e.g., Dark Souls)"
- "Information-dense — all decision-relevant data always visible (e.g., Diablo IV, StarCraft II)"
- "Adaptive — HUD density responds to combat state, exploration mode, menus (e.g., God of War)"

This philosophy becomes the design constraint for every subsequent HUD decision.
If a proposed element conflicts with the stated philosophy, surface that conflict.

---

#### Section B: Information Architecture

Complete this before any layout work. Do not skip it.

**Step 1 — Full information inventory**:
Pull all information from GDD UI Requirements sections gathered in Phase 2.
Present the full list: "These are all the things your game systems say they need
to communicate to the player on screen."

**Step 2 — Categorization**:
Categorize each item by rule:

| Category | Description |
|----------|-------------|
| **Must Show** | Always visible, player needs it for core decisions |
| **Contextual** | Visible only when relevant (in combat, near interactable, etc.) |
| **On Demand** | Player must actively request it (toggle, hold button) |
| **Hidden** | Communicated through world/audio, never on-screen text |

Must Show is for items the core loop's decisions depend on every moment;
Contextual for state-gated items; On Demand for reference data; Hidden for what
the world or audio already conveys. Work through items in groups of 3-4 and
record each placement with its reason; mark borderline items `[확인 필요]`.
This is the most consequential design decision in the HUD — do not rush it.

**Conflict check**: If the information philosophy (Section A) says "nearly HUD-free"
but the Must Show list is growing long, surface the conflict explicitly:
> "The current Must Show list has [N] items. That may conflict with the HUD-free
> philosophy."

Take the first resolution: reduce the Must Show list to the items the core loop
names, demoting the rest to Contextual. Record the conflict and the demoted items
`[확인 필요]`; revising the philosophy or defining a hybrid stays on record as the
alternative.

---

#### Section C: Layout Zones

Only after the information architecture is recorded, design layout zones.

Base layout on:
- Which items are Must Show (they drive the permanent zone decisions)
- Where player attention naturally goes during gameplay (center-screen for action games,
  corners for strategy games)
- Platform and aspect ratio targets

Offer 2-3 zone arrangements. Include rationale based on the HUD philosophy and the
categorization from Section B.

---

#### Section D: HUD Elements

For each element in the layout, specify:
- Element name and category (Must Show / Contextual / On Demand)
- Content displayed
- Visual form (bar, number, icon, counter, map)
- Update behavior (real-time, event-driven, player-queried)
- Contextual trigger (if not always visible)
- Animation behavior (does it pulse when low? Fade in? Slam in?)

Work element by element. Reference the interaction pattern library if relevant patterns
exist for status displays, resource bars, or cooldown indicators.

---

#### Sections E, F, G: Dynamic Behaviors, Platform Variants, Accessibility

These follow the same structure as the UX spec equivalents. See UX Spec section
guidance for D (States/Variants), E (Interactions), and G (Accessibility).

For the HUD specifically, emphasize:
- Dynamic Behaviors: what causes the HUD to change density mid-gameplay?
- Platform Variants: does mobile/console require different element sizes or positions?

---

### Section Guidance: Interaction Pattern Library Mode

Pattern library authoring is additive and catalog-driven, not linear.

#### Phase 1: Catalog Existing Patterns

Glob `design/ux/*.md` (excluding `interaction-patterns.md`) and read the Component
Inventory and Interaction Map sections of each spec. Extract every interaction
pattern used.

Present the extracted list: "Based on existing UX specs, these patterns are already
in use in the game:"
- [Pattern name]: used in [screen], [screen]
- [etc.]

Patterns that exist in the game but appear in no spec cannot be found from the
repository: add a `[확인 필요]` line to the Gaps section asking for them.

---

#### Phase 2: Formalize Each Pattern

For each pattern (existing or new), document:

```markdown
### [Pattern Name]

**Category**: Navigation / Input / Feedback / Data Display / Modal / Overlay / [other]
**Used In**: [list of screens]

**Description**: [One paragraph explaining what this pattern is and when to use it]

**Specification**:
- [Component behavior]
- [Input mapping]
- [Visual/audio feedback]
- [Accessibility requirements for this pattern]

**When to Use**: [Conditions where this pattern is appropriate]
**When NOT to Use**: [Conditions where another pattern is more appropriate]

**Reference**: [Screenshot path or ASCII example, if available]
```

Work through patterns in groups, drafting each batch from what the existing specs
show.

---

#### Phase 3: Identify Gaps

After cataloging known patterns, answer from the GDD UI Requirements and the
existing specs:
- Which planned screens or interactions need patterns not yet in this library?
- Which patterns in existing specs are inconsistent with each other and should be
  consolidated?

Document gaps in the Gaps section for follow-up.

---

## 5. Cross-Reference Check

Before marking the spec as ready for review, run these checks:

**1. GDD requirement coverage**: Does every GDD UI Requirement that references
this screen have a corresponding element in this spec? Present any gaps.

**2. Pattern library alignment**: Are all interaction patterns used in this spec
referenced by name? If a new pattern was invented during this spec session, flag
it for addition to the pattern library:
> "This spec uses [pattern name], which isn't in the pattern library yet.
> Want to add it now, or flag it as a gap?"

**3. Navigation consistency**: Do the entry/exit points in this spec match the
navigation map in any related specs? Flag mismatches.

**4. Accessibility coverage**: Does the spec address the accessibility tier
committed to in `design/accessibility-requirements.md`? If not, flag open questions.

**5. Empty states**: Does every data-dependent element have an empty state defined?
Flag any that don't.

Present the check results:
> **Cross-Reference Check: [Screen Name]**
> - GDD requirements: [N of M covered / all covered]
> - New patterns to add to library: [list or "none"]
> - Navigation mismatches: [list or "none"]
> - Accessibility gaps: [list or "none"]
> - Missing empty states: [list or "none"]

---

## 6. Handoff

When all sections are written:

### 6a: Update Session State

Update `production/session-state/active.md` with:
- Task: [screen-name] UX spec
- Status: Complete (or In Review)
- File: design/ux/[filename].md
- Sections: All written
- Next: [suggestion]

### 6b: Document Review and Next Step

Close with the one document-level review: the section list, every decision with
its rejected alternatives, every `[확인 필요]` item, and the path with its revert
command. Then state:

> "This spec should be validated with `$ux-review` before it enters the
> implementation pipeline. The Pre-Production gate requires all key screen specs
> to have a review verdict."

Recommended next: `$ux-review [filename]`. Also list: `$ux-design patterns` when
this spec introduced new patterns, and "run `$ux-review` on all completed specs
before `$gate-check pre-production`" when more screens remain.

### 6c: Cross-Link Related Specs

If other UX specs link to or from this screen, note which ones should reference
this spec. Those files are outside this run's write scope — name them, do not
edit them.

---

## 7. Recovery & Resume

If the session is interrupted (compaction, crash, new session):

1. Read `production/session-state/active.md` — it records the current screen
   and which sections are complete.
2. Read `design/ux/[filename].md` — sections with real content are done;
   sections with `[To be designed]` still need work.
3. Resume from the next incomplete section — no need to re-discuss completed ones.

This is why incremental writing matters: every approved section survives any
disruption.

---

## 8. Specialist Agent Routing

This skill uses `ux-designer` as the primary agent (set in frontmatter). For
specific sub-topics, additional context or coordination may be needed:

| Topic | Coordinate with |
|-------|----------------|
| Visual aesthetics, color, layout feel | `art-director` — UX spec defines zones; art defines how they look |
| Implementation feasibility (engine constraints) | `ui-programmer` — before finalizing component inventory |
| Gameplay data requirements | `game-designer` — when data ownership is unclear |
| Narrative/lore visible in the UI | `narrative-director` — for flavor text, item names, lore panels |
| Accessibility tier decisions | Handled by this session — owned by ux-designer |

When delegating to another agent as a Codex subagent:
- Provide: screen name, game concept summary, the specific question needing expert input
- The agent returns analysis and decision items to this session
- This session decides within the autonomy contract, records the agent's output
  and the decision in the report, and writes to file
- Agents do NOT write to files directly — this session owns all file writes

---

## Collaborative Protocol

This skill follows the autonomy contract (`rules/autonomy-contract.md`) at every step:

1. **Context -> Derive -> Decide -> Draft -> Write -> Record** for every section
2. **Write, then report**: the skeleton and every section land in the file as they
   are done; the report carries each path and its revert command
3. **One document-level review** at handoff (Phase 6b), not one per section
4. **Incremental writing**: each section is written to file immediately
5. **Session state updates**: after every section write

**Aesthetic deference**: When layout or visual choices come down to personal taste,
take the option consistent with the existing specs and the art bible, record the
alternatives, and mark the choice `[확인 필요]`. The user is the creative director;
one edit reverts the choice.

**Conflict surfacing**: When a GDD requirement and the available screen real estate
conflict, surface the conflict, take the resolution that keeps every requirement
reachable (demote to Contextual or On Demand before dropping), and record the
alternatives. Never silently drop a requirement. Never silently expand the layout
without flagging it.

**Never** write a section without showing where its decisions come from.
**Never** contradict an existing approved UX spec without flagging the conflict.
**Always** show where decisions come from (GDD requirements, player journey, existing specs).

Verdict: **COMPLETE** — UX spec written section by section; `[확인 필요]` items listed in the report.

---

## Recommended Next Steps

- Run `$ux-review [filename]` to validate this spec before it enters the implementation pipeline
- Run `$ux-design [next-screen]` to continue designing remaining screens or flows
- Run `$gate-check pre-production` once all key screens have approved UX specs
