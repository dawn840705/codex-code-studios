---
name: team-release
description: "Orchestrate the release team: coordinates release-manager, qa-lead, devops-engineer, and producer to execute a release from candidate to deployment."
---
**Argument check:** If no version number is provided:
1. Read `production/session-state/active.md` and the most recent file in `production/milestones/` (if they exist) to infer the target version.
2. If a version is found: report "No version argument provided — inferred [version] from milestone data. Proceeding." The version is confirmed at the Phase 6 stop, before anything irreversible runs.
3. If no version is discoverable (K2): stop with Verdict: **BLOCKED** — version unresolved; re-run `$team-release <version>` (e.g., v1.0.0). Do NOT default to a hardcoded version string.

When this skill is invoked, orchestrate the release team through a structured pipeline.

**Decision Points:** Proceed through phases autonomously. Record each phase's
decision and the alternatives rejected in the final report; stop only on K1/K2
or a gate exit 2 (`rules/autonomy-contract.md`).

## Team Composition
- **release-manager** — Release branch, versioning, changelog, deployment
- **qa-lead** — Test sign-off, regression suite, release quality gate
- **devops-engineer** — Build pipeline, artifacts, deployment automation
- **security-engineer** — Pre-release security audit (invoke if game has online/multiplayer features or player data)
- **analytics-engineer** — Verify telemetry events fire correctly and dashboards are live
- **community-manager** — Patch notes, launch announcement, player-facing messaging
- **producer** — Go/no-go decision, stakeholder communication, scheduling

## How to Delegate

Use the Codex subagent mechanism to spawn each team member as a subagent:
- `subagent_type: release-manager` — Release branch, versioning, changelog, deployment
- `subagent_type: qa-lead` — Test sign-off, regression suite, release quality gate
- `subagent_type: devops-engineer` — Build pipeline, artifacts, deployment automation
- `subagent_type: security-engineer` — Security audit for online/multiplayer/data features
- `subagent_type: analytics-engineer` — Telemetry event verification and dashboard readiness
- `subagent_type: community-manager` — Patch notes and launch communication
- `subagent_type: producer` — Go/no-go decision, stakeholder communication
- `subagent_type: network-programmer` — Netcode stability sign-off (invoke if game has multiplayer)

Always provide full context in each agent's prompt (version number, milestone status, known issues). Launch independent agents in parallel where the pipeline allows it (e.g., Phase 3 agents can run simultaneously).

## Pipeline

### Phase 1: Release Planning
Delegate to **producer**:
- Confirm all milestone acceptance criteria are met
- Identify any scope items deferred from this release
- Set the target release date and communicate to team
- Output: release authorization with scope confirmation

### Phase 2: Release Candidate
Delegate to **release-manager**:
- Cut release branch from the agreed commit
- Bump version numbers in all relevant files
- Generate the release checklist using `$release-checklist`
- Freeze the branch — no feature changes, bug fixes only
- Output: release branch name and checklist

### Phase 3: Quality Gate (parallel)
Delegate in parallel:
- **qa-lead**: Execute full regression test suite. Test all critical paths. Verify no S1/S2 bugs. Sign off on quality.
- **devops-engineer**: Build release artifacts for all target platforms. Verify builds are clean and reproducible. Run automated tests in CI.
- **security-engineer** *(if game has online features, multiplayer, or player data)*: Conduct pre-release security audit. Review authentication, anti-cheat, data privacy compliance. Sign off on security posture.
- **network-programmer** *(if game has multiplayer)*: Sign off on netcode stability. Verify lag compensation, reconnect handling, and bandwidth usage under load.

### Phase 4: Localization, Performance, and Analytics
Delegate (can run in parallel with Phase 3 if resources available):
- Verify all strings are translated (delegate to **localization-lead** if available)
- Run performance benchmarks against targets (delegate to **performance-analyst** if available)
- **analytics-engineer**: Verify all telemetry events fire correctly on release build. Confirm dashboards are receiving data. Check that critical funnels (onboarding, progression, monetization if applicable) are instrumented.
- Output: localization, performance, and analytics sign-off

### Phase 5: Go/No-Go
Delegate to **producer**:
- Collect sign-off from: qa-lead, release-manager, devops-engineer, security-engineer (if spawned in Phase 3), network-programmer (if spawned in Phase 3), and technical-director
- Evaluate any open issues — are they blocking or can they ship?
- Make the go/no-go call
- Output: release decision with rationale

**If producer declares NO-GO:**
- Surface the decision: "PRODUCER: NO-GO — [rationale, e.g., S1 bug found in Phase 3]."
- **Skip Phase 6 entirely** — do not tag, deploy to staging, deploy to production, or spawn community-manager.
- Produce a partial report summarizing Phases 1–5, what was skipped (Phase 6) and why, and the fix that would unblock re-running the affected phase. Overriding a NO-GO is a K1 decision: it needs the user's written justification and a re-run.
- Verdict: **BLOCKED** — release not deployed.

A GO from the producer is a decision item, not deployment authorization. Deployment is R4 (`rules/verify-route.md`): it never runs unattended.

### Phase 6: Deployment (if GO)
Write the reversible artifacts first, without asking:
- **release-manager**: generate the changelog using `$changelog`
- **community-manager** (in parallel): finalize patch notes using `$patch-notes [version]`; prepare the launch announcement (store page updates, social media, community post); draft a known-issues post if any S3+ issues shipped. Output: all player-facing release communication, ready to publish on deploy confirmation

Then **stop (K1, R4)** before anything irreversible. Present the go decision, the release checklist, the changelog, the patch notes, and the exact commands that would tag, deploy, and submit. Wait for the user's explicit approval; until it arrives, end with Verdict: **BLOCKED** — awaiting release approval for [version].

After approval, delegate to **release-manager** + **devops-engineer**:
- Tag the release in version control
- Deploy to staging for final smoke test
- Deploy to production
- Monitor for 48 hours post-release

### Phase 7: Post-Release
- **release-manager**: Generate release report (what shipped, what was deferred, metrics)
- **producer**: Update milestone tracking, communicate to stakeholders
- **qa-lead**: Monitor incoming bug reports for regressions
- **community-manager**: Publish all player-facing communication, monitor community sentiment
- **analytics-engineer**: Confirm live dashboards are healthy; alert if any critical events are missing
- Schedule post-release retrospective if issues occurred

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

All file writes (release checklists, changelogs, patch notes, deployment
scripts) are delegated to sub-agents and sub-skills. This orchestrator does not
write files directly. Each sub-agent writes only within its owned paths
(`rules/subagent-collaboration.md` § 3) and returns the paths written; list
every path with its revert command (`git checkout -- <path>`) in the final
report.

## Output

A summary report covering: release version, scope, quality gate results, go/no-go decision, deployment status, and monitoring plan.

Verdict: **COMPLETE** — release executed and deployed.
Verdict: **BLOCKED** — release halted; go/no-go was NO, deployment approval is pending, or a hard blocker is unresolved.

## Next Steps

- Monitor post-release dashboards for 48 hours.
- Run `$retrospective` if significant issues occurred during the release.
- Update `production/stage.txt` to `Live` after successful deployment.
