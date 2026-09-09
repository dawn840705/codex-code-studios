# Autonomy Contract — 기본값은 진행, 멈추는 조건은 열거한다

**Global rule. Applies to every project and every domain.**

높은 주도성을 가진 모델에게 "매 단계 물어보라"는 지시는 두 가지 중 하나로 끝난다.
하네스가 그 지시를 기각해 스킬 전체의 신뢰도가 떨어지거나, 모델이 따르느라
되돌릴 수 있는 파일 하나를 쓰기 전에도 멈춘다. 둘 다 낭비다. 이 규칙은 *언제
멈추는가*를 한 곳에 못 박고, 스킬·역할 가이드·훅이 그 기준을 따르게 한다.

정본은 이 파일이다. 같은 절이 `docs/AGENTS-template.md`(소비 프로젝트의
`AGENTS.md`에 복사되는 원형)와 `CLAUDE.md`(호환 레이어)에 그대로 들어 있다.
세 곳은 글자까지 같아야 한다. 고칠 때는 이 파일을 고치고 두 곳에 복사한다.

---

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

---

## 정지점을 분류하는 법

스킬을 쓰거나 고칠 때, 사용자에게 묻는 문장을 만나면 넷 중 하나로 분류한다.

| 분류 | 예 | 처리 |
|---|---|---|
| **K1 권한** | 유료 호출, 릴리스·배포·삭제·마이그레이션(R4), 확정 결정 번복, 엔진·플랫폼·컨셉처럼 취향과 전략이 결과를 좌우하는 선택, 트랙 미확정 | **멈춘다.** `BLOCKED`와 함께 무엇이 있어야 재개되는지 적는다 |
| **K2 정보 부재** | 필수 입력 파일이나 인자가 없고 저장소 안에서 스스로 찾을 수 없다 | **멈춘다.** 스스로 찾을 수 있으면 K2가 아니다 |
| **K3 사람만 관측** | 수동 플레이테스트·QA 결과, 시각 채택 | **묻되 종료 보고에 묶는다.** 진행을 막지 않는다 |
| **R 되돌릴 수 있는 것** | `design/ production/ docs/ product/` 규약 경로의 산출물 쓰기, 파이프라인 Phase 전환, 옵션 선택, 섹션 초안 승인 | **쓰고 진행하고 보고한다.** 경로와 되돌리기 명령(`git checkout -- <path>` 또는 `git revert`)을 남긴다 |

옵션 A/B/C를 제시하는 자리는 기본값을 선언한다: "다른 조건이 없으면 A를 택하고,
벗어나면 이유를 보고서에 적는다". 쓰기를 거부당했다고 `BLOCKED`를 내지 않는다.
거부는 되돌리기이지 차단이 아니다.

---

## 관련 규칙

- [`verify-route.md`](verify-route.md) — R1~R4. 이 계약의 "R4"가 무엇인지 정의한다
- [`route-hint.md`](route-hint.md) — 몇 개를 부를지. light = 0 agents
- [`decision-lifecycle.md`](decision-lifecycle.md) — 확정 결정은 에이전트가 뒤집지 않는다
- [`subagent-collaboration.md`](subagent-collaboration.md) § 3.1 — 서브에이전트는 결정 항목과 산출물 경로를 반환한다
- [`self-loop.md`](self-loop.md) § 2.1 — 결함 티켓 없는 재작성 금지
- [`work-records.md`](work-records.md) § 2 — 사람만 할 수 있는 일을 쌓는 곳
- 배경: [`docs/design/v0.8.0-astra-autonomy-plan.md`](../docs/design/v0.8.0-astra-autonomy-plan.md)
