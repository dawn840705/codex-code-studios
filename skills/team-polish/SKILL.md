---
name: team-polish
description: "Orchestrate the polish team: coordinates performance-analyst, technical-artist, sound-designer, and qa-tester to optimize, polish, and harden a feature or area for release quality."
---
If no argument is provided, output usage guidance and exit without spawning any agents:
> Usage: `$team-polish [feature or area]` — specify the feature or area to polish (e.g., `combat`, `main menu`, `inventory system`, `level-1`). Do not ask the user directly here; output the guidance directly.

When this skill is invoked with an argument, orchestrate the polish team through a structured pipeline.

**Decision Points:** Proceed through phases autonomously. Record each phase's
decision and the alternatives rejected in the final report; stop only on K1/K2
or a gate exit 2 (`rules/autonomy-contract.md`).

## Team Composition
- **performance-analyst** — Profiling, optimization, memory analysis, frame budget
- **engine-programmer** — Engine-level bottlenecks: rendering pipeline, memory, resource loading (invoke when performance-analyst identifies low-level root causes)
- **technical-artist** — VFX polish, shader optimization, visual quality
- **sound-designer** — Audio polish, mixing, ambient layers, feedback sounds
- **tools-programmer** — Content pipeline tool verification, editor tool stability, automation fixes (invoke when content authoring tools are involved in the polished area)
- **qa-tester** — Edge case testing, regression testing, soak testing

## How to Delegate

Use the Codex subagent mechanism to spawn each team member as a subagent:
- `subagent_type: performance-analyst` — Profiling, optimization, memory analysis
- `subagent_type: engine-programmer` — Engine-level fixes for rendering, memory, resource loading
- `subagent_type: technical-artist` — VFX polish, shader optimization, visual quality
- `subagent_type: sound-designer` — Audio polish, mixing, ambient layers
- `subagent_type: tools-programmer` — Content pipeline and editor tool verification
- `subagent_type: qa-tester` — Edge case testing, regression testing, soak testing

Always provide full context in each agent's prompt (target feature/area, performance budgets, known issues). Launch independent agents in parallel where the pipeline allows it (e.g., Phases 3 and 4 can run simultaneously).

## Pipeline

### Phase 1: Assessment
Delegate to **performance-analyst**:
- Profile the target feature/area using `$perf-profile`
- Identify performance bottlenecks and frame budget violations
- Measure memory usage and check for leaks
- Benchmark against target hardware specs
- Output: performance report with prioritized optimization list

### Phase 2: Optimization
Delegate to **performance-analyst** (with relevant programmers as needed):
- Fix performance hotspots identified in Phase 1
- Optimize draw calls, reduce overdraw
- Fix memory leaks and reduce allocation pressure
- Verify optimizations don't change gameplay behavior
- Output: optimized code with before/after metrics

If Phase 1 identified engine-level root causes (rendering pipeline, resource loading, memory allocator), delegate those fixes to **engine-programmer** in parallel:
- Optimize hot paths in engine systems
- Fix allocation pressure in core loops
- Output: engine-level fixes with profiler validation

### Phase 3: Visual Polish (parallel with Phase 2)
Delegate to **technical-artist**:
- Review VFX for quality and consistency with art bible
- Optimize particle systems and shader effects
- Add screen shake, camera effects, and visual juice where appropriate
- Ensure effects degrade gracefully on lower settings
- Output: polished visual effects

### Phase 4: Audio Polish (parallel with Phase 2)
Delegate to **sound-designer**:
- Review audio events for completeness (are any actions missing sound feedback?)
- Check audio mix levels — nothing too loud or too quiet relative to the mix
- Add ambient audio layers for atmosphere
- Verify audio plays correctly with spatial positioning
- Output: audio polish list and mixing notes

### Phase 5: Hardening
Delegate to **qa-tester**:
- Test all edge cases: boundary conditions, rapid inputs, unusual sequences
- Soak test: run the feature for extended periods checking for degradation
- Stress test: maximum entities, worst-case scenarios
- Regression test: verify polish changes haven't broken existing functionality
- Test on minimum spec hardware (if available)
- Output: test results with any remaining issues

### Phase 6: Sign-off
- Collect results from all team members
- Compare performance metrics against budgets
- Report: READY FOR RELEASE / NEEDS MORE WORK
- List any remaining issues with severity and recommendations

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

All file writes (performance reports, test results, evidence docs) are delegated
to sub-agents spawned as a Codex subagent. This orchestrator does not write
files directly. Each sub-agent writes only within its owned paths
(`rules/subagent-collaboration.md` § 3) and returns the paths written; list
every path with its revert command (`git checkout -- <path>`) in the final
report.

## Output

A summary report covering: performance before/after metrics, visual polish changes, audio polish changes, test results, and release readiness assessment.

## Next Steps

- If READY FOR RELEASE: run `$release-checklist` for the final pre-release validation.
- If NEEDS MORE WORK: schedule remaining issues in `$sprint-plan update` and re-run `$team-polish` after fixes.
- Run `$gate-check` for a formal phase gate verdict before handing off to release.
