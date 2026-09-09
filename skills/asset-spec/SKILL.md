---
name: asset-spec
description: "Generate per-asset visual specifications and AI generation prompts from GDDs, level docs, or character profiles. Produces structured spec files and updates the master asset manifest. Run after art bible and GDD/level design are approved, before production begins."
---

If no argument is provided, check whether `design/assets/asset-manifest.md` exists:
- If it exists: read it, find the first context (system/level/character) with any asset at status "Needed" but no spec file written yet, report "No argument — speccing the next unspecced context: **[target]**", and proceed with it.
- If no manifest: fail with:
  > "Usage: `$asset-spec system:<name>` — e.g., `$asset-spec system:tower-defense`
  > Or: `$asset-spec level:iron-gate-fortress` / `$asset-spec character:frost-warden`
  > Run after your art bible and GDDs are approved."

---

## Phase 0: Parse Arguments

Extract:
- **Target type**: `system`, `level`, or `character`
- **Target name**: the name after the colon (normalize to kebab-case)
- **Review mode**: `--review [full|lean|solo]` if present

**Mode behavior:**
- `full` (default): spawn both `art-director` and `technical-artist` in parallel
- `lean`: spawn `art-director` only — faster, skips technical constraint pass
- `solo`: no agent spawning — main session writes specs from art bible rules alone. Use for simple asset categories or when speed matters more than depth.

---

## Phase 1: Gather Context

Read all source material **before** asking the user anything.

### Required reads:
- **Art bible**: Read `design/art/art-bible.md` — fail if missing:
  > "No art bible found. Run `$art-bible` first — asset specs are anchored to the art bible's visual rules and asset standards."
  Extract: Visual Identity Statement, Color System (semantic colors), Shape Language, Asset Standards (Section 8 — dimensions, formats, polycount budgets, texture resolution tiers).

- **Technical preferences**: Read `.codex/studio/technical-preferences.md` — extract performance budgets and naming conventions.

### Source doc reads (by target type):
- **system**: Read `design/gdd/[target-name].md`. Extract the **Visual/Audio Requirements** section. If it doesn't exist or reads `[To be designed]`:
  > "The Visual/Audio section of `design/gdd/[target-name].md` is empty. Run `$design-system [target-name]` to complete the GDD first."
  Stop: Verdict: **BLOCKED** — source requirements missing (K2).
- **level**: Read `design/levels/[target-name].md`. Extract art requirements, asset list, VFX needs, and the art-director's production concept specs from Step 4.
- **character**: Read `design/narrative/characters/[target-name].md` or search `design/narrative/` for the character profile. Extract visual description, role, and any specified distinguishing features.

### Optional reads:
- **Existing manifest**: Read `design/assets/asset-manifest.md` if it exists — extract already-specced assets for this target to avoid duplicates.
- **Related specs**: Glob `design/assets/specs/*.md` — scan for assets that could be shared (e.g., a common UI element specced for one system might apply here too).

### Present context summary:
> **Asset Spec: [Target Type] — [Target Name]**
> - Source doc: [path] — [N] asset types identified
> - Art bible: found — Asset Standards at Section 8
> - Existing specs for this target: [N already specced / none]
> - Shared assets found in other specs: [list or "none"]

---

## Phase 2: Asset Identification

From the source doc, extract every asset type mentioned — explicit and implied.

**For systems**: look for VFX events, sprite references, UI elements, audio triggers, particle effects, icon needs, and any "visual feedback" language.

**For levels**: look for unique environment props, atmospheric VFX, lighting setups, ambient audio, skybox/background, and any area-specific materials.

**For characters**: look for sprite sheets (idle, walk, attack, death), portrait/avatar, VFX attached to abilities, UI representation (icon, health bar skin).

Group assets into categories:
- **Sprite / 2D Art** — character sprites, UI icons, tile sheets
- **VFX / Particles** — hit effects, ambient particles, screen effects
- **Environment** — props, tiles, backgrounds, skyboxes
- **UI** — HUD elements, menu art, fonts (if custom)
- **Audio** — SFX, music tracks, ambient loops *(note: audio specs are descriptions only — no generation prompts)*
- **3D Assets** — meshes, materials (if applicable per engine)

Record the full grouped list in the report ("Identified [N] assets across [N] categories for **[target]**") and proceed to Phase 3 with all of them. An asset the user later removes or adds is one edit to the spec file and the manifest.

---

## Phase 3: Spec Generation

Spawn specialist agents based on review mode. **Issue all Codex subagent calls simultaneously — do not wait for one before starting the next.**

### Full mode — spawn in parallel:

**`art-director`** as a Codex subagent:
- Provide: full asset list from Phase 2, art bible Visual Identity Statement, Color System, Shape Language, the source doc's visual requirements, and any reference games/art mentioned in the art bible Section 9
- Ask: "For each asset in this list, produce: (1) a 2–3 sentence visual description anchored to the art bible's shape language and color system — be specific enough that two different artists would produce consistent results; (2) a generation prompt ready for use with AI image tools (Midjourney/Stable Diffusion style — include style keywords, composition, color palette anchors, negative prompts); (3) which art bible rules directly govern this asset (cite by section). For audio assets, describe the sonic character instead of a generation prompt."

**`technical-artist`** as a Codex subagent:
- Provide: full asset list, art bible Asset Standards (Section 8), technical-preferences.md performance budgets, engine name and version
- Ask: "For each asset in this list, specify: (1) exact dimensions or polycount (match the art bible Asset Standards tiers — do not invent new sizes); (2) file format and export settings; (3) naming convention (from technical-preferences.md); (4) any engine-specific constraints this asset type must respect; (5) LOD requirements if applicable. Flag any asset type where the art bible's preferred standard conflicts with the engine's constraints."

### Lean mode — spawn art-director only (skip technical-artist).

### Solo mode — skip both. Derive specs from art bible rules alone, noting that technical constraints were not validated.

**Collect both responses before Phase 4.** If any conflict exists between art-director and technical-artist (e.g., art-director specifies 4K textures but technical-artist flags the engine budget requires 512px), surface it explicitly — do NOT silently resolve.

---

## Phase 4: Compile and Review

Combine the agent outputs into a draft spec per asset, in this format:

```
## ASSET-[NNN] — [Asset Name]

| Field | Value |
|-------|-------|
| Category | [Sprite / VFX / Environment / UI / Audio / 3D] |
| Dimensions | [e.g. 256×256px, 4-frame sprite sheet] |
| Format | [PNG / SVG / WAV / etc.] |
| Naming | [e.g. vfx_frost_hit_01.png] |
| Polycount | [if 3D — e.g. <800 tris] |
| Texture Res | [e.g. 512px — matches Art Bible §8 Tier 2] |

**Visual Description:**
[2–3 sentences. Specific enough for two artists to produce consistent results.]

**Art Bible Anchors:**
- §3 Shape Language: [relevant rule applied]
- §4 Color System: [color role — e.g. "uses Threat Blue per semantic color rules"]

**Generation Prompt:**
[Ready-to-use prompt. Include: style keywords, composition notes, color palette anchors, lighting direction, negative prompts.]

**Status:** Needed
```

Self-review every spec against the art bible before writing. Revise inline only where a specific art bible rule is violated (cite the section) — do NOT re-spawn agents for text revisions; re-spawn only if the visual direction itself contradicts the art bible. Record each revision and its rule in the report. The written file is the single document-level review point.

---

## Phase 5: Write Spec File

Write the spec to `design/assets/specs/[target-name]-assets.md`. Report the path and the revert command (`git checkout -- <path>`).

Write the file with:

```markdown
# Asset Specs — [Target Type]: [Target Name]

> **Source**: [path to source GDD/level/character doc]
> **Art Bible**: design/art/art-bible.md
> **Generated**: [date]
> **Status**: [N] assets specced / [N] approved / [N] in production / [N] done

[all asset specs in ASSET-NNN format]
```

Then update `design/assets/asset-manifest.md`. If it doesn't exist, create it:

```markdown
# Asset Manifest

> Last updated: [date]

## Progress Summary

| Total | Needed | In Progress | Done | Approved |
|-------|--------|-------------|------|----------|
| [N] | [N] | [N] | [N] | [N] |

## Assets by Context

### [Target Type]: [Target Name]
| Asset ID | Name | Category | Status | Spec File |
|----------|------|----------|--------|-----------|
| ASSET-001 | [name] | [category] | Needed | design/assets/specs/[target]-assets.md |
```

If the manifest already exists, append the new context block and update the Progress Summary counts.

Update `design/assets/asset-manifest.md` in the same pass and report it with the spec path.

---

## Phase 6: Close

For anchor-based 3D assets, include the anchor hash, identity/anatomy constraints,
intended camera, project budgets and required clips in the production handoff.
When production is requested, route through `$studio-orchestrator` and
[`../../docs/anchor-to-3d-workflow.md`](../../docs/anchor-to-3d-workflow.md).
Speccing an asset does not itself authorize generation, paid calls or retries.

Close with: "Asset specs complete for **[target]** — [N] assets, [paths]." Recommended next: `$asset-spec [next unspecced context from the manifest]`, or `$asset-audit` once assets are delivered.

---

## Asset ID Assignment

Asset IDs are assigned sequentially across the entire project — not per-context. Read the manifest before assigning IDs to find the current highest number:

```
Grep pattern="ASSET-" path="design/assets/asset-manifest.md"
```

Start new assets from `ASSET-[highest + 1]`. This ensures IDs are stable and unique across the whole project.

If no manifest exists yet, start from `ASSET-001`.

---

## Shared Asset Protocol

Before speccing an asset, check if an equivalent already exists in another context's spec:

- Common UI elements (health bars, score displays) are often shared across systems
- Generic environment props may appear in multiple levels
- Character VFX (hit sparks, death effects) may reuse a base spec with color variants

If a match is found: reference the existing ASSET-ID rather than creating a duplicate. Note the shared usage in the manifest's referenced-by column.

> "ASSET-012 (Generic Hit Spark) already specced for Combat system. Reusing for Tower Defense — adding tower-defense to referenced-by."

---

## Error Recovery Protocol

If any spawned agent returns BLOCKED or cannot complete:

1. Record it in the report: "[AgentName]: BLOCKED — [reason]"
2. In `lean` mode or if `technical-artist` blocks: proceed with art-director output only — note that technical constraints were not validated
3. In `solo` mode or if `art-director` blocks: derive descriptions from art bible rules — flag as "Art director not consulted — verify against art bible before production"
4. Always produce a partial spec — never discard work because one agent blocked

---

## Collaborative Protocol

Every phase follows: **Identify → Generate → Self-review → Write → Report**

- Record the identified asset list before speccing — it is the report's first table
- Always anchor specs to the art bible — a spec that contradicts the art bible is wrong
- Surface all agent disagreements in the report — pick the art-bible-compliant one and name the other
- Write the spec file, then report its path and revert command
- Update the manifest immediately after writing the spec
- Speccing never authorizes generation: paid calls go through `$api-cost-gate`

---

## Recommended Next Steps

- Run `$asset-spec [next-context]` to continue speccing remaining systems, levels, or characters
- Run `$asset-audit` to validate delivered assets against the written specs and identify gaps or mismatches
