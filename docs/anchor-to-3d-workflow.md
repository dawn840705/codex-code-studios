# Anchor-based 3D art workflow

Adopted 2026-09-07 after a user-requested art, technical-art and workflow review
of a completed stylized armored-creature pilot. The review supported character
identity and the generation/editing/export process. It did not establish a
repeatable success rate across assets or engine readiness.

## Scope and entry

Use this route when the user requests an approved visual anchor to become a 3D
asset through consistent views, a generator such as Tripo, Blender editing and,
when needed, rigging and animation. The initial validated scope is stylized
armored creatures. Other body types, soft deformation, hard-surface precision or
close-up hero assets require an explicit asset-specific pilot and criteria.

Run through `$studio-orchestrator`; `$asset-spec` supplies the asset contract and
`$asset-audit` checks delivered evidence. This document is the production route,
not a new public skill or an automatic batch-generation service. An advisory
review does not authorize production; use the user's actual requested scope.

Read the project's approved art bible and asset specification first. Record the
anchor path and hash, identifying silhouette, color regions, anatomy and counts,
intended camera/usage, units and forward/up axes, geometry/material/texture
budgets, required clips and deformation tolerances. Resolve these from the
project; never copy a pilot's dimensions, bone coordinates or budgets as defaults.

Keep one owner for live Blender mutations. Independent art and technical review
can run in parallel on immutable evidence. Preserve existing unsaved scenes
before import. Follow [artifact organization](rules/artifact-organization.md)
for storage, provenance, editable sources and cross-machine recovery.

## Stage gates

1. **Lock the anchor.** Preserve the actual approved image. Derived views remain
   modeling references and do not replace the visual source of truth. List the
   few traits whose loss would make this a different character.
2. **Prepare front, back, left and right views.** Request orthographic cameras,
   zero pitch/roll, consistent scale, pose, lighting, grounding and framing.
   Inspect each result: direction labels alone do not prove camera alignment.
   Check landmark heights, silhouette proportions, limb/attachment counts,
   left/right asymmetry and occlusion. Distinguish hidden anatomy from missing
   anatomy. Reject incompatible views before a paid model request. If a small
   mismatch is accepted for an editable draft, record the mismatch, reason and
   asset-specific tolerance; do not call it a precision orthographic drawing.
3. **Generate one authorized model.** Read `$api-cost-gate` before any paid
   image or 3D call. Verify the current endpoint, accepted view ordering, model,
   options and price through the available provider interface/documentation.
   Dry-run first where supported. Use the existing approved cap and retry scope;
   a workflow adoption is not a new spending approval. Record actual input bytes,
   sanitized request, task ID, balances, charge and output hashes. No automatic
   paid retry. Image generation and 3D generation have separate cost records.
4. **Inspect and repair in Blender.** Preserve the raw model and work on a
   separate editable copy using Blender MCP. Inspect actual geometry, axes,
   units, UVs, materials and topology before editing. Compare several views and
   an untextured render. UV/normal splits are not necessarily separate parts;
   do not blindly weld them. Correct identity or anatomy defects first, then
   grounding and local surface defects. Preserve accepted regions and original
   texture data. A visible defect justifies a bounded fix, not endless redesign.
5. **Rig and animate when required.** Fit joints to this mesh. Test one limb
   before extending the rig; verify protected regions stay still and weights
   remain normalized and consistent across UV seams. Check articulated armor,
   joint limits, unwanted intersections, foot contact and sliding through motion.
   Record intended root motion or in-place matching speed. Create only required
   clips and keep visual timing separate from gameplay event wiring.
6. **Save, export and reopen independently.** Reopen the saved editable file
   and verify its intended scene survives; an in-memory scene is not evidence
   of a valid saved deliverable. Limit exports to the intended scene and asset
   objects. Bake constraints as needed. In a separate process import each target
   format, then check geometry, UVs, weights, deform bones, textures and clips.
   Compare poses at equal clip-relative elapsed time, accounting for format
   start-frame offsets. Test both bake samples and times between samples, plus
   contact and loop boundaries. Increase sample density only if measured error
   requires it; record tolerance in meaningful units relative to asset scale.
   Identify importer-generated helper objects by their actual references before
   counting them as exported meshes. Keep failures and corrected results.
7. **Review and hand off.** Present the anchor, comparable model views, material
   and clay evidence, required motion previews, measured results and remaining
   visual defects. Ask for visual adoption only when it is still required by
   the project and not already given. If engine integration is authorized,
   verify the real game camera, materials, import scale, clips and platform
   budget there. A file roundtrip cannot substitute for that engine check.

## Decisions and stopping rules

- Report **workflow adoption**, **individual visual adoption**, **exchange-file
  verification**, **engine verification** and **spending authorization** separately.
- Identity/anatomy failure, incompatible views, unreadable saved source, broken
  dependencies or deformation beyond the agreed tolerance blocks that stage.
- Boundary cleanup, facet sharpening, small claw/horn refinements or motion
  polish may remain if the intended use and visual decision accept them. For
  close-up use the same defect can become a blocker. Do not invent similarity
  percentages from unmatched cameras or turn a render comparison into an
  unmeasured fidelity score.
- A prototype can establish a useful route while engine suitability and wider
  repeatability remain untested. Do not declare all assets production-ready
  from one successful character. Additional pilots need their own assignment
  and any required cost approval; do not launch them merely to fill a checklist.
- Follow [self-loop](../rules/self-loop.md) for bounded repairs and
  [verification routing](../rules/verify-route.md) for independent review. Do not
  weaken a failing criterion to make an export pass.

## Evidence to retain

Keep the accepted anchor and view bytes, hashes and generation provenance;
raw model and final editable source; asset-specific settings and script order;
exchange files and texture dependencies; comparison/motion evidence; failure
history and final checks; actual charges; remaining defects and explicit
adoption states. Use the project's storage/recovery policy rather than an
expiring download URL or one machine's path. Prompts are not byte-exact recovery.

Service/model versions, prices, polygon/texture counts, rig layouts, axis choices,
clip lengths, sample rates and tolerances belong in each asset's record. Preserve
the reusable checks here, not private project files or specimen-specific code.
