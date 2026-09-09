# Project AGENTS.md template

Copy the contents below into a consumer project's root `AGENTS.md` and tailor it
to the repository. Commit shared team rules; keep machine-specific secrets and
credentials out of this file.

```markdown
# Project guide

## Product and stack

- Track: game | product
- Engine/framework and pinned version:
- Target platforms:
- Architecture source of truth:

## Working agreements

- Run the relevant tests after code changes.
- Preserve existing user changes and avoid destructive cleanup.
- Record major technical choices as ADRs.
- Keep `production/session-state/active.md` current during multi-session work.

## 자율 계약 (Autonomy contract)

기본값은 진행이다. 라우트(`rules/route-hint.md`)와 검증 등급(`rules/verify-route.md`)을 스스로 정하고 실행한다.
멈추고 사람에게 넘기는 조건은 다음뿐이다. 이 밖의 판단은 묻지 않고 내린다:

- R4 (되돌릴 수 없거나 사용자에게 비용이 가는 변경) · 유료 API 호출 (`$api-cost-gate`)
- 트랙 미확정 (`production/track.txt` 없음. 한 번 묻고 기록한다)
- `AGENTS.md` 확정 결정을 뒤집는 일 (`rules/decision-lifecycle.md` § 4) · 쓰기 소유 밖 파일
- 사람만 관측할 수 있는 사실 (수동 플레이테스트·QA 결과). 질문은 종료 보고에 묶는다
- 사용자가 명시적으로 검토·승인을 요구한 항목

진행할 때의 의무: 라우트·R등급을 한 줄로 기록한다 · 되돌리기 경로를 남긴다 (커밋 단위, 폐기 표시) ·
검증은 exit code로 증명한다 (`docs/deterministic-gates.md`) · 결함 티켓 없는 재작성은 하지 않는다 (`rules/self-loop.md` § 2.1).
서브에이전트는 질문 대신 **결정 항목**(안건·권고·대안·근거·되돌리기 비용)을 반환하고, 오케스트레이터가 위 조건 안에서 결정한다.
스킬은 **산출물 계약**(무엇을 어디에 만들고 무엇으로 끝났다고 판정하는가)이지 절차 대본이 아니다. 절차는 스스로 정한다.
사람만 할 수 있는 일은 `production/human-actions.md`에 쌓는다 (`rules/work-records.md` § 2). BLOCKED는 실패가 아니다.

## Code Studios policy feedback

- Source checkout (configure for this project):
- When a confirmed working agreement or verified prevention measure also applies
  to other projects, follow `docs/policy-updates.md` in the source checkout and
  update the relevant rule, skill, or template during task closeout.
- Keep product-specific decisions here. Record the source commit and distinguish
  source changes from the plugin version actually installed.

## Local commands

- Build:
- Unit tests:
- Integration tests:
- Lint/format:

## Communication

- Lead with outcomes and verification evidence.
- Surface decisions that require product or design authority.
```

Code Studios stores engine and naming preferences separately in
`.codex/studio/technical-preferences.md`; `$setup-engine` can create it.
