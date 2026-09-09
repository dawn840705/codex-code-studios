---
name: team-level
description: "Orchestrate level design team: level-designer + narrative-director + world-builder + art-director + systems-designer + qa-tester for complete area/level creation."
---

When this skill is invoked:

**Decision Points:** Proceed through phases autonomously. Record each phase's
decision and the alternatives rejected in the final report; stop only on K1/K2
or a gate exit 2 (`rules/autonomy-contract.md`).

1. **Read the argument** for the target level or area (e.g., `tutorial`,
   `forest dungeon`, `hub town`, `final boss arena`).

2. **Gather context**:
   - Read the game concept at `design/gdd/game-concept.md`
   - Read game pillars at `design/gdd/game-pillars.md`
   - Read existing level docs in `design/levels/`
   - Read relevant narrative docs in `design/narrative/`
   - Read world-building docs for the area's region/faction

## How to Delegate

Use the Codex subagent mechanism to spawn each team member as a subagent:
- `subagent_type: narrative-director` — Narrative purpose, characters, emotional arc
- `subagent_type: world-builder` — Lore context, environmental storytelling, world rules
- `subagent_type: level-designer` — Spatial layout, pacing, encounters, navigation
- `subagent_type: systems-designer` — Enemy compositions, loot tables, difficulty balance
- `subagent_type: art-director` — Visual theme, color palette, lighting, asset requirements
- `subagent_type: accessibility-specialist` — Navigation clarity, colorblind safety, cognitive load
- `subagent_type: qa-tester` — Test cases, boundary testing, playtest checklist

Always provide full context in each agent's prompt (game concept, pillars, existing level docs, narrative docs).

3. **Orchestrate the level design team** in sequence:

### Step 1: Narrative + Visual Direction (narrative-director + world-builder + art-director, parallel)

Spawn all three agents simultaneously — issue all three Codex subagent calls before waiting for any result.

Spawn the `narrative-director` agent to:
- Define the narrative purpose of this area (what story beats happen here?)
- Identify key characters, dialogue triggers, and lore elements
- Specify emotional arc (how should the player feel entering, during, leaving?)

Spawn the `world-builder` agent to:
- Provide lore context for the area (history, faction presence, ecology)
- Define environmental storytelling opportunities
- Specify any world rules that affect gameplay in this area

Spawn the `art-director` agent to:
- Establish visual theme targets for this area — these are INPUTS to layout, not outputs of it
- Define the color temperature and lighting mood for this area (how does it differ from adjacent areas?)
- Specify shape language direction (angular fortress? organic cave? decayed grandeur?)
- Name the primary visual landmarks that will orient the player
- Read `design/art/art-bible.md` if it exists — anchor all direction in the established art bible

**The art-director's visual targets from Step 1 must be passed to the level-designer in Step 2** as explicit constraints. Layout decisions happen within the visual direction, not before it.

**Checkpoint**: Record all three Step 1 outputs (narrative brief, lore foundation, visual direction targets) in the final report. Continue to Step 2.

### Step 2: Layout and Encounter Design (level-designer)
Spawn the `level-designer` agent with the full Step 1 output as context:
- Narrative brief (from narrative-director)
- Lore foundation (from world-builder)
- **Visual direction targets (from art-director)** — layout must work within these targets, not contradict them

The level-designer should:
- Design the spatial layout (critical path, optional paths, secrets) — ensuring primary routes align with the visual landmark targets from Step 1
- Define pacing curve (tension peaks, rest areas, exploration zones) — coordinated with the emotional arc from narrative-director
- Place encounters with difficulty progression
- Design environmental puzzles or navigation challenges
- Define points of interest and landmarks for wayfinding — these must match the visual landmarks the art-director specified
- Specify entry/exit points and connections to adjacent areas

**Adjacent area dependency check**: After the layout is produced, check `design/levels/` for each adjacent area referenced by the level-designer. If any referenced area's `.md` file does not exist, surface the gap:
> "Level references [area-name] as an adjacent area but `design/levels/[area-name].md` does not exist."

Proceed with a placeholder reference: mark the connection UNRESOLVED in the level doc, list it in the open cross-level dependencies section of the summary report, and add `$team-level [area-name]` to Next Steps. Do NOT invent content for the missing adjacent area.

**Checkpoint**: Record the Step 2 layout (including unresolved adjacent-area dependencies) in the final report. Continue to Step 3.

### Step 3: Systems Integration (systems-designer)
Spawn the `systems-designer` agent to:
- Specify enemy compositions and encounter formulas
- Define loot tables and reward placement
- Balance difficulty relative to expected player level/gear
- Design any area-specific mechanics or environmental hazards
- Specify resource distribution (health pickups, save points, shops)

**Checkpoint**: Record the Step 3 outputs in the final report. Continue to Step 4.

### Step 4: Production Concepts + Accessibility (art-director + accessibility-specialist, parallel)

**Note**: The art-director's directional pass (visual theme, color targets, mood) happened in Step 1. This pass is location-specific production concepts — given the finalized layout, what does each specific space look like?

Spawn the `art-director` agent with the finalized layout from Step 2:
- Produce location-specific concept specs for key spaces (entrance, key encounter zones, landmarks, exits)
- Specify which art assets are unique to this area vs. shared from the global pool
- Define sight-line and lighting setups per key space (these are now layout-informed, not directional)
- Specify VFX needs that are specific to this area's layout (weather volumes, particles, atmospheric effects)
- Flag any locations where the layout creates visual direction conflicts with the Step 1 targets — surface these as production risks

Spawn the `accessibility-specialist` agent in parallel to:
- Review the level layout for navigation clarity (can players orient themselves without relying on color alone?)
- Check that critical path signposting uses shape/icon/sound cues in addition to color
- Review any puzzle mechanics for cognitive load — flag anything that requires holding more than 3 simultaneous states
- Check that key gameplay areas have sufficient contrast for colorblind players
- Output: accessibility concerns list with severity (BLOCKING / RECOMMENDED / NICE TO HAVE)

Wait for both agents to return before proceeding.

**Checkpoint**: Record both Step 4 results in the final report. If the accessibility-specialist returned any BLOCKING concern, send the flagged elements back to level-designer and art-director for one redesign pass before Step 5. If a BLOCKING concern survives that pass, log it as a known accessibility gap in the level doc and the final report and proceed; name the reason in the report.

### Step 5: QA Planning (qa-tester)
Spawn the `qa-tester` agent to:
- Write test cases for the critical path
- Identify boundary and edge cases (sequence breaks, softlocks)
- Create a playtest checklist for the area
- Define acceptance criteria for level completion

4. **Compile the level design document** combining all team outputs into the
   level design template format.

5. **Save to** `design/levels/[level-name].md`.

6. **Output a summary** with: area overview, encounter count, estimated asset
   list, narrative beats, any cross-team dependencies or open questions, open
   cross-level dependencies (adjacent areas referenced but not yet designed, each
   marked UNRESOLVED), and accessibility concerns with their resolution status.

## File Write Protocol

All file writes (level design docs, narrative docs, test checklists) are
delegated to sub-agents spawned as a Codex subagent. This orchestrator does not
write files directly. Each sub-agent writes only within its owned paths
(`rules/subagent-collaboration.md` § 3) and returns the paths written; list
every path with its revert command (`git checkout -- <path>`) in the final
report.

Verdict: **COMPLETE** — level design document produced and all team outputs compiled.
Verdict: **BLOCKED** — one or more agents blocked; partial report produced with unresolved items listed.

## Next Steps

- Run `$design-review design/levels/[level-name].md` to validate the completed level design doc.
- Run `$dev-story` to implement level content once the design is approved.
- Run `$qa-plan` to generate a QA test plan for this level.

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
