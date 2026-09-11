# Code Studios contributor guide

This repository is the source package for the `codex-code-studios` Codex plugin.

## Source of truth

- `.codex-plugin/plugin.json` defines the Codex plugin.
- `.agents/plugins/marketplace.json` defines the local/shareable marketplace entry.
- `skills/*/SKILL.md` contains user-facing workflows. Keep every skill valid under the Codex skill format.
- `skills/studio-orchestrator/references/roles/*.md` contains specialist personas. They are references loaded by the orchestrator, not independently installed Codex agents.
- `hooks/hooks.json` and `hooks/*.sh` implement Codex lifecycle hooks.
- `rules/*.md`, `docs/`, and `templates/` are plugin resources. They are not Codex command-approval rule files.

## Runtime modes

This studio ships twice: `codex-code-studios` (Codex, `$skill-name`) and the
sibling `claude-code-studios` (Claude Code, `/skill-name`). A user project may
be worked by one alone or by both at once, and that decides whether this plugin
acts at all.

`production/runtime.txt` in the user's project is the source of truth — one
line: `codex` (full studio, default) · `claude` (stand down; the sibling owns
the work) · `split` (work only the partition this runtime owns). Absent means
`codex`. Never infer the mode from a `CLAUDE.md` or `.claude/` sighting.

In `split` mode, write ownership is partitioned **by path** before work starts.
The two runtimes share no session, context or tool log, so an overwrite is
invisible to both and the losing side still reports success. Full rule:
[`rules/runtime-modes.md`](rules/runtime-modes.md).

## Change rules

1. Preserve existing public skill names unless a migration explicitly documents a rename.
2. Use `$skill-name` when referring to a Codex skill invocation.
3. Resolve bundled resources relative to the invoking `SKILL.md` or `PLUGIN_ROOT`; reserve `.codex/` for state stored in the user's project.
4. Keep hook stdout valid for the matching Codex hook event. Advisory PostToolUse feedback belongs in `hookSpecificOutput.additionalContext`.
5. Run the plugin validator, every skill validator, the skill linter, shell syntax checks, and the full test suite before release.
6. When changing asset tracking, ignore rules, or cross-machine handoff workflows, read [Artifact Organization Rules](docs/rules/artifact-organization.md), including the shared asset recovery requirements.

The legacy `.claude-plugin/` manifest and `CLAUDE.md` remain only as a transition compatibility layer for the 0.7 release. Do not make them the source of truth for new Codex behavior.

## 프로젝트에서 확인한 방침의 지속 반영

- 프로젝트 진행 중 확정된 공통 운영 원칙과 검증된 재발 방지 절차는 이 원본 저장소에 계속 반영한다. 사용자 직접 지시 근거: 2026-09-07, 새 코드 스튜디오 프로젝트에 앞으로 가져갈 방침을 업데이트하라는 요청.
- 반영 시 [공통 방침 갱신 절차](docs/policy-updates.md)를 읽고 따른다. 기존 규칙·스킬·템플릿의 실제 적용 위치를 갱신하고 중복 정본을 만들지 않는다.
- 특정 제품의 기획·수치·개인 경로·역할 계약은 공통 기본값으로 승격하지 않는다. 원본 변경과 설치된 플러그인 적용 상태를 따로 보고한다.
