# 27회 비교 실험 준비 — 2026-09-07

상태: **실행기·검증·고정 snapshot 준비 완료, 실제 모델 실행 0회**.
이번 후속 요청 시작 시 계정 주간 사용률은 97%(잔여 약 3%)였다. 리셋/구매/
전역 설정 변경 없이 오프라인 준비를 진행했다. 이전의 교란된 3회 파일럿은
별도 기록으로 보존하고 이번 표본에 합치지 않는다.

## 준비된 실행 범위

| 항목 | 값 |
|---|---|
| 고정 모델 | gpt-6-astra |
| 초기 commit | cada722a9900cb57c312467f3c19ee6315b0ce33 |
| 소스 트리 해시 | f71cb54c8dbf85e054e579bb977ad18a010975b58ef946da3f772ec88cb826fa |
| 작업 | 스킬 파일 개수, plugin version 문자열, hook event 이름의 정렬된 JSON 배열 |
| 설정 | 고정 Medium / 고정 High / 자동 선택 |
| 반복 | 작업별 설정당 3회, 총 27회 |
| 순서 | seed 20260907, 각 작업 안에서 세 설정이 각 실행 위치에 한 번씩 오도록 순환 |
| 실행 제한 | 읽기 전용, 자동 재시도 0, 모델 프로세스당 timeout 60초 |
| 검증 | snapshot에서 사전 계산한 정답 + 최종 agent_message + 파일 상태 해시 |

현재 세 작업은 범위·영향·불확실성이 낮고 검증 가능한 기계적 작업이다.
따라서 auto는 Low를 선택한다. 이 실험은 Low 허용 구간의 기초 비교이며
복잡한 설계/디버깅에서 Medium/High/Xhigh 기준을 보정하는 실험은 아니다.

## 보강한 실행 계약

`tests/effort_pilot.py`에 추가했다.

- plan의 작업 정의/정답, 일정, 실행 상한을 다시 계산하여 변경을 감지한다.
- Python/플랫폼/CLI 경로·버전/사용자 config 내용 해시를 준비 시 기록하고
  시작 전과 각 실행 사이에 다시 비교한다. config 원문과 인증 파일은 기록하지 않는다.
- 회귀 테스트를 먼저 끝낸 뒤 `--standalone`을 명시해야 실행한다. 이 플래그는
  운영자의 확인 기록이며 다른 프로세스나 서버 부하를 자동 차단하는 기능이 아니다.
- 3회를 넘는 배치는 **새로 확인한 계정 잔여량 10% 이상**을 입력해야 시작한다.
  10%는 아직 보정되지 않은 운영상 가설이며, 27회가 반드시 그 안에 끝난다는
  보장/토큰 예산/청구 상한이 아니다. 실제 권한과 여유를 확인하여 실행한다.
- 잔여량이 없거나 부족하면 dispatch 표식을 만들기 전에 거부한다. 리셋을
  소비하거나 다른 모델로 바꾸는 대안은 자동 실행하지 않는다.
- executor 실패/소스 변경/환경 변경 시 이후 실행을 중단한다. batch 재실행과
  애매한 종료 후 자동 재시도는 하지 않는다.
- 텍스트 정답은 정확히 비교하며 JSON 배열은 공백 차이는 허용하고 순서는 검사한다.
- 작업/설정별 계획 수, 시도 수, 성공 수·비율, 시간 median, 실행 토큰 부분합을
  집계한다. 실패를 제외하지 않으며 사용량 결측을 0으로 대체하지 않는다.
- 분류 규칙의 실제 실행 시간/추가 모델 토큰 0을 기록한다. 부모가 조사·범위를
  판단한 비용은 여전히 미계측이어서 null로 남긴다. total_usage와 절감 주장은
  자동 계산하지 않는다. cached input은 input에 다시 더하지 않는다.

설치된 plugin cache/호스트 문맥, 원격 모델 alias·서버 부하·공유 cache는
완전 고정하지 못한다. 이 한계를 environment 기록에도 남긴다. 각 verifier는
별도 60초 timeout을 쓰므로 모델 timeout이 전체 배치의 시간 상한은 아니다.

## 검증 결과

| 검사 | 증거 |
|---|---|
| 집중 정책 검사 | `62 passed in 2.98s`, exit 0 |
| 27회 전체 실행 흐름 | 실제 모델 없이 로컬 fake CLI로 27회 실행, 9개 그룹 각각 3/3 성공; 파일 상태 보존 |
| 파일럿 전용 검사 | `python3 -m pytest -q tests/test_effort_pilot.py` → `9 passed in 4.79s`, exit 0 |
| 전체 회귀 검사 | `651 passed, 5 skipped, 40 subtests passed in 49.03s`, exit 0 |
| 정책 축 | `verify_policy.py --project-root .` → `COMPLIANT — 0 abort, 0 warning`, exit 0 |
| 실제 준비본의 잔여량 차단 | `remaining_percent=3` → `expanded pilot requires ... >=10`; dispatch-claim 없음 |

27회 fake 실행의 성공/시간/토큰은 실행기 검증용 합성 값이다. 실제 모델의
성공률이나 절감률로 인용하지 않는다. 이번에 live 모델을 추가 호출하지 않았다.

검증 루프: 1회, 결함으로 인한 재작성 없음. 이 단계의 품질 기준과 한계:

| 기준 | 점수 | 근거 | 남은 리스크 |
|---|---:|---|---|
| 반복·순서·정답 일치 | 9 | 27 dispatch/9 groups의 오프라인 검사 exit 0 | 실제 반복 실험 미실행 |
| 실행 전 잔여량·환경 방어 | 8 | 잔여 3%에서 dispatch 전 거부; 변경 환경 거부 테스트 | 잔여 입력은 운영자 확인값, 서버 부하 통제 불가 |
| 비용·실패 집계의 정직성 | 8 | 실패 포함 비율·결측 null·cache 중복 미합산 테스트 | 부모 분류 비용 미계측 |
| 기존 회귀·정책 보존 | 9 | 전체 651 passed 및 정책 exit 0 | 기존 skip 5개 유지 |

## 준비본과 재개 절차

현재 로컬 준비본:
`.codex/reasoning-effort/experiment-20260907-02/manifest.json`.
snapshot과 원시 기록은 Git에서 제외한다. 설정 원문/인증정보를 문서로 옮기지 않는다.

계정 여유와 실행 승인 범위를 확인한 뒤, 회귀 테스트가 모두 끝난 상태에서만
다음 명령을 사용한다. `실측잔여퍼센트`에는 방금 조회한 실제 숫자를 넣으며
통과시키기 위해 임의 값을 넣지 않는다.

```bash
python3 tests/effort_pilot.py run \
  --output .codex/reasoning-effort/experiment-20260907-02 \
  --remaining-percent 실측잔여퍼센트 --standalone
```

준비 후 CLI/설정/실행기가 달라졌다면 이전 plan을 편집하여 통과시키지 말고 새
output 경로로 `prepare`한다. 실제 배치의 승인 범위를 `--approval-ref`에 기록한다.

```bash
python3 tests/effort_pilot.py prepare \
  --output .codex/reasoning-effort/새로운실험이름 \
  --model gpt-6-astra --supported low medium high xhigh max ultra \
  --cases count-skills manifest-version hook-events --repetitions 3 \
  --approval-ref '실제 승인 기록 참조'
```

완료 후 summary의 작업별 paired 결과와 결측을 검토한다. 이 기계적 표본에서
Low가 통과해도 전체 기본 effort를 낮추지 않는다. 별도 복잡도/경계 holdout과
부모 비용을 포함한 계측이 있어야 다음 정책 보정을 판단할 수 있다.
