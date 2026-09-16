# 요청별 reasoning effort: 조사·설계·최소 구현

조사일: 2026-09-07. 대상: Codex Code Studios. 정책:
`effort-v1-hypothesis`. 상태: **관찰 + 제한된 CLI 전달기**, 성능/절감률 미검증.

후속 진행: [2026-09-07 실제 모델 3회 파일럿](effort-pilot-20260907.md)을 완료했다.
아래의 미실행 설명은 초기 조사 시점 기록이다. 효과 판정은 아직 보류다.
그 다음 [27회 비교 실행기와 준비본](effort-expanded-experiment.md)을 검증했다.
잔여 계정 사용량 부족으로 확장 배치의 실제 모델 호출은 아직 하지 않았다.

## 지원 범위와 구현 위치

기존 앱 입력은 `UserPromptSubmit`으로 자동 관찰할 수 있다. 훅 출력으로
진행 중인 부모 대화의 effort를 바꾸는 인터페이스는 확인되지 않았다.
현재 세션에도 부모 effort 변경 도구가 없다. “High 선택” 기록은 runtime
설정 변경이 아니다.

이 저장소는 앱/게임 실행기가 아닌 Codex 플러그인이다. `AGENTS.md`에 따라
`.codex-plugin/plugin.json`, `skills/`, `hooks/`가 기준이다. 기존
`route-hint`는 에이전트 수, `verify-route`는 검증 강도를 결정하므로 effort를
별도 축으로 추가했다. 91개 공개 스킬/45개 역할 구성과 legacy 파일은 유지한다.

| 경로 | 가능한 설정 전달 | 장점 | 제약 / 이번 범위 |
|---|---|---|---|
| 앱 입력 → 관찰 훅 | prompt, model, session/turn id 제공 | 기존 입력 흐름, 추가 모델 호출 없음 | UI effort·조사된 범위 미제공. 초기 판단은 잠정적 |
| 현재 부모 턴 중 변경 | 현재 도구에 setter 없음; hook output에 effort 필드 없음 | 앱에 정식 지원되면 가장 가까운 경로 | 지원한다고 보고하지 않음. 앱 DB/내부 소켓 수정 안 함 |
| 별도 `codex exec` | CLI 0.153.4: `-m` + `-c model_reasoning_effort=...` | argv 및 HTTP 직렬화 검사 가능 | 별도 문맥·사용량·실행 승인 필요 |
| 서브에이전트 | custom TOML/spawn effort; 현재 `spawn_agent.reasoning_effort` | 부모 대화에서 위임 가능 | 부모/자식/문맥 비용 합산. 현재 full-history fork는 override 불가. 이번에 생성하지 않음 |
| App Server 클라이언트 | `TurnStartParams.effort` | 호스트가 다음 턴 시작 시 전달 가능 | 앱 플러그인 입력 가로채기 API와 다름. 별도 클라이언트/앱 지원 필요 |
| Responses API | Astra standard/single-agent `configuration_update` | 응답 사이 변경과 prefix cache 유지 | Codex 앱 지원 보장 아님. API 실행기는 미구현 |

공식 근거: [Hooks](https://learn.chatgpt.com/docs/hooks),
[설정](https://learn.chatgpt.com/docs/config-file/config-advanced),
[서브에이전트](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[App Server](https://learn.chatgpt.com/docs/app-server),
[Reasoning API](https://developers.openai.com/api/docs/guides/reasoning).

로컬 `codex app-server generate-json-schema`는 exit 0. 생성된
`TurnStartParams.effort` 설명은 “Override the reasoning effort for this turn
and subsequent turns.”였다. `TurnSteerParams`에는 effort가 없다.
`ThreadStartResponse.reasoningEffort`는 설정 응답이지만 생산 모델의 추론
적용 계측과는 다르다. 앱 task 도구의 `thinking`도 별도/후속 작업 실행 인자이며
진행 중인 부모 턴 setter로 취급하지 않는다.

공식 서브에이전트 문서상 custom agent 파일 값이 우선하며, 그 전에 explicit
spawn → `[agents]` default → parent 순서로 결정된다. spawn 인자만 보고
적용값을 단정하면 안 된다. 이번에는 실제 서브에이전트 적용 receipt를 검사하지
않았다. 모델 고정·명시 effort 보존·추가 호출 승인을 만족할 때 별도 연결한다.

## 선행 자료 검토

| 자료 | 확인 결과와 채택 범위 |
|---|---|
| [Ares v1](https://arxiv.org/html/2603.07915v1) | 표 2의 gpt-oss-20b Retail High 54.8%/1007k → RL 58.5%/476k 확인. 추론 토큰 지표이며 Codex/Unity 총비용 절감으로 일반화하지 않음. 이력·도구 증거 반영 참고 |
| [auto-reasoning](https://github.com/luckeyfaraday/auto-reasoning/tree/a70c7c4274391cad2fa298db0f11fbc1eba2c469) | HEAD `a70c7c4` 고정. README, classifier, CLI adapter, harness 읽음. 0.1.x 소개. 설치·실행·전체 보안 감사 안 함 |
| [Adaptive Reasoning Router](https://github.com/blackjose007-stack/adaptive-reasoning-router/tree/71ec619828a0f3ce3ced0888e69486b58c42559a) | HEAD `71ec619`, README 검토. runtime 변경 보장 없음·로그 호출 필요 명시. 경계별 결정 참고. 가중치 기반 반사실 추정은 토큰 실측이 아님. 전체 코드 감사 안 함 |
| [Gearbox #20855](https://github.com/openai/codex/issues/20855) | 조사 시 Open/enhancement. 이유·상한·전환 기록 참고. 제공 중 기능으로 간주하지 않음 |
| [RouteLLM](https://github.com/lm-sys/RouteLLM) | 평가·임계값 보정 참고. 모델 간 라우팅이며 이번 동일 모델 effort 선택과 구분 |
| [過労くん — GPT-6 Astra 절약 설정 5선](https://x.com/karoukun_ai/status/2099834185678782928) | 2026-09-15 X 포스트. OpenAI Help 문서 4건(`help.openai.com/en/articles/20001516` 등, Work/Codex 공유 할당량·모델별 5시간 메시지 한도)을 인용해 Plus 플랜 절약 팁을 정리했다. **원문 help 페이지는 이번에 직접 열람하지 않았다** — 포스트의 인용을 그대로 옮겨 적은 2차 출처로 취급한다. 채택 범위는 아래 절 참고 |

### 2026-09-17 추가 — Astra/Sol/Terra/Luna 할당량 절약 팁 채택

위 포스트가 정리한 5가지 설정 중, 이 저장소에 이미 있는 개념과 겹치지 않고 실무에
바로 적용 가능한 3가지만 반영했다. 반영 위치와 이유:

| 포스트의 팁 | 반영 위치 | 비고 |
|---|---|---|
| 작업 난이도로 모델 고르기 (Astra/Sol/Terra/Luna), 다운그레이드해도 이미 쓴 할당량은 안 돌아온다 | [`rules/route-hint.md`](../rules/route-hint.md) Model axis | 기존 "lane별 standing policy" 원칙을 이미 갖고 있었다. 이번엔 "결정은 시작 전에, 도중 다운그레이드는 환불 없음" 한 줄만 근거로 보강 |
| reasoning은 Low/Medium부터 — 높인다고 항상 좋아지지 않고, 약한 모델의 Low가 강한 모델의 High를 이기기도 한다 | 위와 동일 | 이 저장소의 `rules/reasoning-effort.md`는 "모델은 고정, effort만 변수"라는 별도 축이라 모델 간 비교 주장은 그쪽에 넣지 않았다 |
| 참조 문서는 장면별로 읽을 범위를 지정하고, 매번 전체를 읽히지 않는다 | [`docs/rules/token-efficiency.md`](rules/token-efficiency.md) R7 (신설) | 기존 R1-R6에 없던 축이라 신설 |
| 완료 조건과 위임 범위를 먼저 던지고, 애매한 판단은 끝에 몰아서 보고받는다 | 위와 동일 R8 (신설) | 왕복 확인 감소 — 역시 기존 R1-R6에 없던 축 |

**반영하지 않은 것과 이유:**
- **Fast 모드 끄기** — 이 저장소에는 대응하는 실행 스위치가 없다(오케스트레이터가 호출하는 CLI 실행기에 그런 옵션 없음). 있지도 않은 기능을 문서화하지 않는다.
- **할당량 소진 시 즉시 리셋 구매** — 과금 액션이라 `$api-cost-gate` 범위이지 워크플로 규칙 범위가 아니다.
- **Usage 잔여량 사전 확인** — 유용하지만 이 저장소의 `scripts/reasoning_effort.py`는 Usage API를 조회하지 않는다. 있다고 암시하는 문서를 쓰지 않고, 미구현으로 남긴다.

auto-reasoning의 [CLI adapter](https://github.com/luckeyfaraday/auto-reasoning/blob/a70c7c4274391cad2fa298db0f11fbc1eba2c469/src/adapters/codex-cli.ts)는
effort 뒤에 `extraArgs`를 붙이고 prompt를 위치 인자로 전달한다. 우리 구현은
모델을 명시하고 extraArgs를 없애며 prompt를 stdin으로 전달한다.
[harness](https://github.com/luckeyfaraday/auto-reasoning/blob/a70c7c4274391cad2fa298db0f11fbc1eba2c469/src/core/harness.ts)는
실행/verifier 실패 및 예외 후 effort를 올려 재시도한다. 환경·인증 장애를
추론 부족과 구분하지 못하는 이 동작은 채택하지 않았다. 영어 정규식·단어 수
기반 분류 역시 한국어 짧은 요청에 충분하지 않다. 외부 의존성은 추가하지 않았다.

고정 effort에서도 실제 추론량은 요청마다 달라진다. effort는 고정 토큰
예산/가격표가 아니다. Astra API의 configuration update는 standard,
single-agent에 한정하며 응답 사이 입력으로 다음 응답에 적용한다.
원래 request-level effort를 유지하는 방식은 앱 부모 대화 제어와 별개다.

## 구현과 사용법

- `scripts/reasoning_effort.py`: stdlib 분류, 관찰, 단일 실행과 검증 기록.
- `hooks/observe-effort.sh` + `hooks/hooks.json`: opt-in 입력 관찰.
- `rules/reasoning-effort.md`: 선택·권한·재평가 계약.
- `skills/studio-orchestrator/SKILL.md`: 범위 조사 후 관찰 안내.
- `.codex/reasoning-effort.json`: **이 저장소만** 관찰 활성화.

전역 `~/.codex/config.toml`, 설치된 플러그인 캐시, 다른 프로젝트는 변경하지
않았다. 이미 앱에 로드된 0.7.0 캐시에 새 훅이 즉시 설치된 것은 아니다.
이 소스의 플러그인을 로드/갱신한 후 새 턴에서 훅을 확인해야 한다.
설치 전에도 아래 명령은 이 저장소에서 직접 실행 가능하다.

관찰 설정은 `.codex/reasoning-effort.json`의 `{"mode":"observe"}`다.
파일이 없거나 mode가 다른 값이면 훅은 아무 작업도 하지 않는다. mode를
`execute`로 바꿔도 실행하지 않는다. 구형 호스트에서 훅이 실행되지 않으면
워크플로에서 명시적으로 `observe`를 호출한다.

작업 JSON 예시(값은 실제 조사와 사용자 설정에 맞춘다):

```json
{
  "task_id": "count-skills-001",
  "prompt": "skills/*/SKILL.md 파일 개수를 세고 숫자만 출력해. 파일은 수정하지 마.",
  "model": "gpt-5.5",
  "scope": "single",
  "impact": "low",
  "uncertainty": "low",
  "verification": "deterministic",
  "evidence": ["skills/는 한 단계 하위 디렉터리에 SKILL.md를 둠; 독립 검사 가능"],
  "explicit_effort": null,
  "read_only": true,
  "supported_efforts": ["low", "medium", "high", "xhigh"],
  "required_checks": [["python3", "/absolute/path/to/reviewed-verifier.py", "{events}"]]
}
```

모델은 예시다. 실험 전체에서 모델 하나를 고정하고 지원 effort를 확인한다.
사용자 선택을 알면 `explicit_effort`에 넣는다. UI 값이 안 보인다는 이유로
auto 실행 승인을 추정하지 않는다. `max_effort`는 사용자 상한이다.
자동 선택은 4단계지만 기존 none/minimal/max/ultra 명시 선택도 관찰에서
보존하며 실행은 확인된 지원값만 허용한다. 인용문/“High” 단어는 설정으로
해석하지 않는다. 구체적 가설·실패/경계 규칙은
[reasoning-effort 규칙](../rules/reasoning-effort.md)을 따른다.

```bash
python3 scripts/reasoning_effort.py observe --task /absolute/path/task.json --root .
python3 scripts/reasoning_effort.py observe --task /absolute/path/task.json --root . --arm medium
python3 scripts/reasoning_effort.py observe --task /absolute/path/task.json --root . --arm high
```

출력의 `record`가 결정 파일이다. `run` 기본 동작은 argv 계획 출력이다.
`--execute`를 추가해야 별도 CLI를 실행한다. 아래 승인 참조는 실제 승인
기록으로 교체해야 한다. 문자열 자체가 승인을 만들지 않는다.

```bash
python3 scripts/reasoning_effort.py run --task /absolute/path/task.json \
  --decision /absolute/path/decision.json --root . --approval-ref 'actual approved scope'
# 작업/검증/사용량 범위가 승인된 뒤 같은 명령에 --execute 추가
```

실행 명령은 `codex exec --json --sandbox read-only -C <root> -m <fixed-model>
-c model_reasoning_effort="<selected>" -`이며 argv 배열과 stdin을 사용한다.
생산 경로는 config·rules·hooks를 무시하거나 신뢰/승인을 우회하지 않는다.
부모 세션에만 있는 승인·추가 지시·문맥은 자동 복제되지 않는다. 부모의
금지/범위/검증 조건도 신뢰된 task prompt에 포함해야 한다.

`required_checks`는 승인된 독립 verifier argv다. `{events}`는 실행 JSONL
경로로 치환된다. 모델 답이 맞는지 검사해야 하며 단순 exit 0 스크립트를 live
성공 판정에 쓰면 안 된다. 기존 필수 검사도 모두 포함한다. verifier는 전달기
권한으로 실행되며 CLI sandbox 안에 있지 않으므로 외부 텍스트에서 만들지 않는다.

Low로 분류됐다고 실행 자격이 생기지 않는다. v1 실행은 근거가 있는
single/low/low/deterministic + read_only만 허용한다. 위험 단어/실패가 있으면
거부한다. 자동 재시도는 0회. 실패·timeout 후에도 실행 디렉터리를 남겨 같은
결정의 중복 dispatch를 막는다. 재시도는 원인 조사와 새 승인 범위 확인이 필요하다.

## 기록 계약

`.codex/reasoning-effort/<id>/decision.json`에는 원문 대신 prompt/task/evidence
해시와 구조화된 신호를 기록한다. task_id에는 식별자만 쓴다. 해시는 익명화
보장이 아니며 상세 감사에는 원래 작업 JSON/조사 근거가 필요하다. 동일 hook
session/turn/model/prompt는 중복 기록하지 않는다. 원자적 파일 게시와 배타적
실행 디렉터리 생성으로 부분 쓰기·경합·중복 dispatch를 방어한다.

| 필드 | 의미 |
|---|---|
| candidate_effort | 규칙의 후보 |
| selected_effort | override·상한·안정화·실험 arm 적용 후 선택 |
| passed_effort | 프로세스 시작 시 argv 전달값. 관찰/계획/시작 실패는 null |
| applied_effort | v1은 null. 모델 자기 설명에서 추정하지 않음 |
| application_evidence | 미실행 또는 process argv 수준의 증거 |
| classification_seconds / classification_rule_tokens | 로컬 순수 분류 시간 / 추가 모델 호출 토큰 0 |
| context_assessment_tokens | 부모의 조사·범위 판단 비용. 미계측이면 null |
| execution_usage | CLI 완료 이벤트의 input/cached input/output 합계. 결측/실패면 null |
| reasoning_tokens / total_usage | 상세 추론 토큰 미확인 / 전체 비용 구성 불완전이면 null |
| execution_and_verification_seconds | 프로세스 시작부터 필수 검사 종료까지 벽시계 |
| success | 실행 정상 종료 + 완료 이벤트 + 모든 required_checks exit 0 |
| automatic_retries / rework_count / user_interventions | 0 / 외부 재작업과 개입은 별도 계측 전 null |

실행의 `execution/events.jsonl`과 `stderr.txt`에는 작업/소스가 포함될 수 있다.
run 디렉터리를 제한된 권한으로 만들고 Git에서 제외한다. 서명된 감사는 아니며
강제 종료 시 starting/running으로 남을 수 있다. 자동 복구 실행은 하지 않는다.
로컬 파일시스템 기준이며 네트워크 볼륨/Windows process tree 종료는 추가 검증이
필요하다.

## 검증과 다음 비교 실험

최종 명령·수치는 [검증 기록](reasoning-effort-validation.md)에 둔다.
정책 fixture의 “저장 고쳐” + cross/high/high → Xhigh 같은 기대값은 가설의
회귀 기준이지 최적 effort의 정답 라벨이 아니다.

실 CLI wire probe는 동일 gpt-5.5/`Reply probe`/빈 임시 작업 상태에서
Medium/High/Auto(Low)/명시 Xhigh를 검사한다. 수신기는 model과 effort를
검사하고 HTTP 400 `LOCAL_PROBE_NO_INFERENCE`를 반환한다. CLI exit 1은
의도한 결과, pytest exit 0이 전달 검증 성공이다. 모델 적용/성능/과금 비교가
아니다. 이 테스트만 임시 실행에 ignore-user-config와 loopback provider를
사용하며 실제 설정 파일은 변경하지 않는다. 생산 전달기에 이 옵션은 없다.

다음 라이브 실험은 아래 순서로 한다.

1. 모델·CLI·정책/스킬/AGENTS·prompt·검증기·초기 commit·환경·권한을 고정한다.
   새 유료/계정 사용량 호출 수·시간·예산을 기존 승인과 대조한다. 이번에는 새
   추론 배치의 구체적 승인이 없어 외부 모델 호출을 하지 않았다.
2. 각 arm마다 같은 commit의 새 임시 clone/worktree를 만든다. 미커밋 변경은
   검토된 별도 snapshot을 복제한다. 사용자 checkout을 reset하지 않는다.
   신뢰·캐시·추가 문맥 조건과 모델 alias 변경 가능성도 기록한다.
3. 첫 파일럿은 스킬 개수/manifest 필드/문서 링크의 read-only 작업 3개 ×
   3 arm × 3회 = 27회 제안(미승인·미실행). 독립 verifier를 먼저 작성한다.
   사용자 명시 effort 사례는 override 테스트로 분리하여 arm 비교에서 제외한다.
4. arm 순서를 반복마다 무작위 배치하고 seed를 기록한다. 고정 arm도 동일한
   로깅 코드를 거친다. auto의 부모 범위 판단과 CLI 문맥 재로딩 비용을 포함한다.
5. [측정 템플릿](templates/effort-measurement.json)에 각 실행의 성공, 전체
   벽시계, 분류/실행/검증/재시도/부모·자식 사용량, 재작업·개입을 채운다.
   output에 포함된 reasoning, input에 포함된 cached input을 중복 합산하지
   않는다. 누락은 0 대신 null. 실패·timeout도 표본에 남긴다.
6. arm별 성공/시도 수, 시간 median/p95, 전체 input+output, 재작업·개입과
   paired task 차이를 비교한다. 성공한 실행만 골라 평균 내지 않는다. 작은
   표본의 성공률 우열을 단정하지 않는다. 품질 비열등 허용폭·채택 기준은 사전
   결정한다. 실제 청구액/단가 기반 추정/effort 가중치 추정을 별개 열에 둔다.
7. 파일럿과 별도 holdout으로 기본값과 Low 조건을 보정한다. 짧은 한국어,
   인증/권한, 저장 포맷, 마이그레이션, 동시성, 검증 불가능, 환경 장애, 새 증거를
   포함한다. 현재 실행 자격 밖의 사례는 관찰부터 하고 별도 검토 후 확장한다.

이번에 실제 모델의 성공률·시간·총사용량·비용 절감 비교는 수행하지 않았다.
전용 분류 모델/RL/상시 서버/앱 내부 패치는 필요성이 입증될 때만 검토한다.

유료 호출 기준은 [`skills/api-cost-gate/SKILL.md`](../skills/api-cost-gate/SKILL.md):
“Do **not** make the API call until the user responds with explicit approval.”
사전 승인 배치는 그 범위 내 재질문하지 않는다. 이번에는 로컬 전달 검증까지
수행했으므로 추가 비용 승인을 요청하지 않았다.
