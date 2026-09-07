---
name: studio-orchestrator
description: "Route a multi-stage game or software request to the smallest useful set of Code Studios specialist roles, coordinate Codex subagents, and apply the repository's quality gates. Use for cross-discipline work, team workflows, or when the user asks the studio to own an outcome. Do not use for a focused task that one existing workflow skill can complete directly."
---

# Studio Orchestrator

Use this skill when a request spans disciplines or benefits from specialist review. For a focused request, invoke the matching workflow skill directly and avoid unnecessary delegation.

## 1. Establish the track and stage

1. Read `production/track.txt` when it exists.
2. Treat `game` as the game-development track and `product` as the app, web, or service track.
3. If the track cannot be inferred safely and changes the requested outcome, ask the user.
4. Inspect existing plans, milestones, specifications, and recent changes before staffing work.

For an approved visual anchor → consistent views → generated 3D model → Blender
editing/rigging/animation request, read
[`../../docs/anchor-to-3d-workflow.md`](../../docs/anchor-to-3d-workflow.md).
Use its staged production and verification route within the user's authorized
scope; workflow adoption alone does not authorize new paid calls.

## 2. Choose the lightest route

- **Light:** handle the task in the current agent with one workflow skill.
- **Standard:** delegate one bounded subtask to one specialist role.
- **Heavy:** fan out independent subtasks to multiple specialist roles, then integrate and verify.

Prefer fewer calls. Parallelize only work that is genuinely independent, and keep one integration owner.

When the project opts into effort observation with `.codex/reasoning-effort.json`,
follow `../../rules/reasoning-effort.md` after inspecting scope. Record a decision
at task boundaries or material new evidence, preserving explicit user settings.
Observation does not change the parent's runtime effort or authorize another run.

## 3. Load specialist roles

Role guides live in `references/roles/`. Select only the roles required for the outcome. Read each selected role guide, then include its relevant responsibilities and constraints in the self-contained prompt passed to the Codex subagent. A role guide is context, not a separately installed agent.

Use `references/role-index.md` to discover roles. Stage presets remain in `../../docs/agent-packs.yaml`.

## 4. Delegate safely

For every subagent prompt, include:

- the concrete deliverable and acceptance criteria;
- the exact files or subsystem in scope;
- relevant project decisions and selected role guidance;
- whether the assignment is read-only or may edit files;
- the evidence and tests required at handoff.

Do not delegate strategic choices that require user authority. Do not let two editing agents own the same files concurrently.
Ask before writing to user-owned files when the selected workflow is advisory or
the request did not authorize implementation.

## 5. Integrate and verify

Review subagent evidence, resolve conflicts, and run deterministic checks before qualitative review. Follow `../../rules/verify-route.md`, `../../rules/self-loop.md`, and `../../docs/director-gates.md`. A clear quality criterion is iterative: execute, score with evidence, fix the weakest criterion, and stop when every criterion reaches the documented threshold or the iteration guard fires.

## 6. Report

Lead with the completed outcome, list material decisions and verification evidence, and call out any unresolved user decision. End with `COMPLETE` when the requested outcome and required checks are finished, or `BLOCKED` with the exact missing authority or dependency.

## Recommended next

Suggest another workflow skill only when it is genuinely useful; otherwise stop.
