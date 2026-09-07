# Reasoning effort 검증 기록

2026-09-07, macOS, Python 3, Codex CLI `0.153.4`.
작업 시작 HEAD: `cada722` (`main`). 검사 대상은 미커밋 작업 트리다.
결과: **최소 관찰/전달 구현 완료**, 실제 모델 성능·총비용 비교는 미실행.
설치 캐시와 전역 설정을 바꾸거나 플러그인을 배포하지 않았다.

후속 요청으로 [실제 모델 3회 파일럿](effort-pilot-20260907.md)을 진행했다.
그 결과와 최신 전체 테스트(647 passed)는 해당 기록을 참조한다.

## 재현 가능한 검사

| 검사 | 실행 / 결과 |
|---|---|
| 전체 테스트 | `python3 -m pytest -q tests/` → **exit 0**, `642 passed, 5 skipped, 40 subtests passed in 44.67s` |
| 실제 CLI 요청 직렬화 | 아래 opt-in 명령 → **exit 0**, `4 passed in 6.75s` |
| 플러그인 validator | 시스템 plugin-creator의 `scripts/validate_plugin.py .` → **exit 0**, `Plugin validation passed` |
| 모든 스킬 validator | 시스템 skill-creator의 `scripts/quick_validate.py`를 `skills/*/SKILL.md`의 각 부모에 실행 → **91/91 valid**, exit 0 |
| 모든 스킬/역할 linter | `python3 scripts/lint_skills.py skills/ skills/studio-orchestrator/references/roles/ --baseline` → **exit 0**, 136개 검사 |
| 변경 스킬 static | `python3 scripts/lint_skills.py skills/studio-orchestrator --baseline scripts/lint_baseline.json` → **exit 0**, `1 COMPLIANT, 0 WARNINGS, 0 NON-COMPLIANT` |
| shell syntax | `hooks/**/*.sh` 18개에 `bash -n` → **전부 exit 0** |
| 정책 축 | `python3 scripts/verify_policy.py --project-root .` → **exit 0**, `COMPLIANT — 0 abort, 0 warning` |
| 정책 self-test | `python3 scripts/verify_policy.py --self-test` → **exit 0**, `self-test passed` |
| 라우팅 회귀 | `python3 scripts/verify_trajectory.py` → **exit 0**, `MATCH — 13 phases unchanged` |
| 생성물 일치 | `build_quick_rules.py --check`, `build_diagnosis_rules.py --check` → **exit 0**, 최신 |
| workflow schema | `python3 scripts/check_phase.py --validate` → **exit 0**, `VALID: 2 track(s), 82 steps` |
| diff 공백 검사 | `git diff --check` → **exit 0** |

전체 기본 실행의 skip 5개는 opt-in CLI probe 4개와 기존 로컬 측정 fixture 1개다.
별도 probe 실행으로 4개를 검증했고, 기존 fixture의 skip은 그대로 보고한다.
새 테스트를 제외하거나 기존 실패를 baseline에 추가하지 않았다.

전체 linter에는 기존 경고/부채가 남는다:
`5 COMPLIANT, 123 WARNINGS, 0 NON-COMPLIANT (of 136) — 8 baselined failure(s) tolerated`.
이는 경고 0건이라는 뜻이 아니다. 이번 변경 스킬은 별도 검사에서도 경고 0이다.

```bash
# 외부 추론 호출 없음. 설치된 codex의 절대 경로를 명시한다.
CODE_STUDIOS_TEST_CODEX=/Applications/ChatGPT.app/Contents/Resources/codex \
  python3 -m pytest -q tests/test_reasoning_effort_cli_wire.py
```

## 선택 / 전달 / 적용의 증거 수준

| 검사 | 모델 / 요청 / 상태 | 선택 | 로컬 HTTP에서 받은 effort | 생산 모델 적용 |
|---|---|---|---|---|
| 고정 Medium | gpt-5.5 / Reply probe / 빈 임시 root | medium | medium | 미검증 |
| 고정 High | 동일 | high | high | 미검증 |
| 자동 | 동일 | low | low | 미검증 |
| 사용자 명시 | 동일 | xhigh | xhigh | 미검증 |

실제 CLI가 `reasoning.effort`를 직렬화했음을 검사한다. loopback 서버는
HTTP 400 `LOCAL_PROBE_NO_INFERENCE`를 반환한다. 이때 CLI exit 1은
의도한 결과이며, 그 결과와 전달값을 검증한 **pytest exit 0**이 판정이다.
가짜 서버는 추론하지 않았으므로 위 표에서 성공률/절감률을 계산하지 않는다.
6.75초는 테스트 하네스 시간이며 실제 작업의 완료 시간 비교가 아니다.

가짜 CLI 단위 테스트에서는 입력이 stdin으로 그대로 전달되고 모델/effort가
argv에 들어가는지, 두 완료 이벤트의 사용량이 합산되는지 검사한다.
예제의 27 input / 8 cached input / 8 output은 **합성 테스트 값**이다.
모델 텍스트가 `applied high`라고 말해도 `applied_effort`는 null로 남는다.

이 프로젝트 자체의 실제 관찰 기록도 생성했다:
`.codex/reasoning-effort/0baff95e0d934a088f26fa8a80f35ddc/decision.json`.
`selected_effort=high`, `passed_effort=null`, `applied_effort=null`.
이 파일은 프로젝트 로컬 상태여서 Git에 포함하지 않는다. 작업의 부모 runtime을
바꿨다는 증거가 아니며, 관찰 선택만 수행했다.

## 자체 점검 2회

첫 회차의 전체 테스트는 **exit 1**:
`3 failed, 632 passed, 5 skipped, 40 subtests passed in 44.11s`.

| 결함 | 증거 | 수정 범위 |
|---|---|---|
| 새 CLI 실제 콘솔 시나리오 누락 | `test_every_entry_point_has_a_real_run_scenario[reasoning_effort.py]` 실패 | 새 observe 시나리오 추가 |
| 비ASCII 출력 계약 미충족 | `test_non_ascii_output_survives_every_encoding[reasoning_effort.py]` 실패 | 한국어 help + 기존 force_utf8 재사용 |
| 테스트 subprocess 디코딩 미지정 | `test_every_text_mode_subprocess_pins_utf8`가 새 테스트 두 곳 식별 | `encoding="utf-8"` 명시 |

정책의 명시 상한 유지/해제, malformed usage의 null 처리도 보강하고 회귀
테스트를 추가했다. 최종 전체 테스트와 별도 실제 CLI probe가 모두 exit 0이다.
검증 범위를 줄여 해결하지 않았다.

| 합격 기준 | 최종 점수 | 판정 / 인용 증거 | 남은 리스크 |
|---|---:|---|---|
| 선택·전달·적용 구분 | 9 | 테스트 exit 0, `applied_effort is None`; wire `4 passed` | 생산 모델 receipt 미검증 |
| override·한국어·실패·경계 정책 | 9 | 전체 exit 0, `test_stability_and_new_evidence`, `test_failure_is_not_automatic_escalation` | 기준은 가설, 최적 effort 라벨 아님 |
| 경합·부분 쓰기·중복 dispatch | 8 | 전체 exit 0, concurrent observations, 반복 hook 동일 bytes, 두 번째 execute의 FileExistsError | 네트워크 FS/Windows 프로세스 트리 미검증 |
| 기존 승인/검증 규칙 유지 | 9 | `COMPLIANT — 0 abort, 0 warning`, `642 passed` | 실제 사용자 승인 유효성은 운영자가 확인해야 함 |
| 기능 경계와 측정 정직성 | 8 | 문서의 “실제 모델의 성공률·시간·총사용량·비용 절감 비교는 수행하지 않았다”; total_usage null 검사 | 실제 비교 성능은 아직 판단 불가 |

정책 축: `verify_policy.py` **exit 0**. 최소 구현 검증은 완료하며 새 유료
호출을 전제로 하는 live 평가와 앱 플러그인 재설치/재로딩 확인은 남아 있다.
다음 실험의 고정 조건·표본·측정 항목·승인 범위는
[조사 및 실험 방법](reasoning-effort.md#검증과-다음-비교-실험)을 따른다.
