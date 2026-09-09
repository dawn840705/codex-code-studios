---
name: doc-relink
description: "Documentation reorganization without breaking links — baseline the current rot, `git mv`, then let scripts/doc_relink.py rewrite every affected markdown link deterministically (exit code is the verdict, the model never hand-edits link paths). Use when moving/renaming docs, folders, or consolidating scattered documents; when the user says '문서 옮겨', '폴더 정리', 'move the docs', 'fix broken links', '링크 깨졌어', 'doc refactor'. Born from a 705-doc reorg (2026-08-13) that rewrote 265 links with zero new breaks."
---

# Doc Relink — 문서 이동은 스크립트가, 판단은 모델이

문서 재편에서 토큰이 새는 지점은 링크 재작성이다. 수백 개 링크를 모델이 훑으면
비싸고 틀린다. 이 스킬의 분업:

- **`scripts/doc_relink.py` 가 손을 댄다.** git rename 매핑을 읽어 링크를
  2패스로 재계산하고, 게이트 판정은 **exit code** 로 낸다. stdout 을 읽고
  성공 여부를 다시 추론하지 말 것.
- **이 스킬(모델)은 판단만 한다.** 무엇을 어디로 옮길지, 이동 금지 제약이
  없는지, 스크립트가 못 다루는 잔여를 어떻게 처리할지.

Writes: `Documents/` 아래 마크다운 링크(및 `--extra` 경로)를 `scripts/doc_relink.py relink` 가 제자리에서 고쳐 쓴다. 모델은 링크를 손으로 편집하지 않는다.

## 절차 (순서가 곧 안전장치다)

```bash
# 0) 이동 전 — 기존 파손을 baseline 으로 고정 (이미 썩어 있던 링크는 게이트 대상이 아니다)
python3 scripts/doc_relink.py check <root> --docs Documents \
    --extra AGENTS.md --extra skills --write-baseline /tmp/links-baseline.txt

# 1) git mv 로 이동 (스테이지 상태 유지 — 커밋하지 말 것. rename 매핑이 여기서 나온다)
git mv "Documents/old/A.md" "Documents/new/"

# 2) 링크 재계산 2패스 (유입 링크 + 이동 파일 자신의 상향 링크)
python3 scripts/doc_relink.py relink <root> --docs Documents \
    --extra AGENTS.md --extra skills

# 3) 게이트 — 신규 파손 0 이면 exit 0
python3 scripts/doc_relink.py check <root> --docs Documents \
    --extra AGENTS.md --extra skills --baseline /tmp/links-baseline.txt
```

판정은 exit code 가 낸다 — **exit 0 = PASS** (신규 파손 없음, 커밋 진행) ·
**exit 1 = FAIL** (신규 파손 목록 출력 — 수리 후 재검) · exit 2 = 사용 오류
(스테이지된 rename 없음 등). stdout 을 읽고 판정을 재해석하지 않는다.

## 이동 전에 모델이 확인할 것 (스크립트 밖의 판단)

1. **이동 금지 제약** — 프로젝트에 경로를 하드코딩한 소비자가 있는가:
   코드가 직접 읽는 폴더(빌드 도구·익스포터), `.gitignore` 의 경로 리터럴 예외,
   플러그인·훅 계약 경로, CI. `grep -rn "<폴더명>"` 을 코드·설정에 먼저 돌린다.
2. **링크 밀도** — 같은 폴더 bare-basename 링크가 수백 건인 폴더(회의록류)는
   쪼개는 순간 전부 깨진다. 재편 대상에서 빼는 것도 답이다.
3. **동시 편집** — 다른 세션·사람이 미커밋 수정 중인 파일은 옮기지 않는다.
   `git status` 로 먼저 확인.

## 스크립트가 못 다루는 것 (모델 몫)

- `](<path with spaces>)` 꺾쇠 링크, reference-style 링크 — 건수를 grep 으로
  세고 손으로 고친다 (보통 0~수 건).
- **폴더 링크** `](SomeDir/)` 가 이동한 폴더를 가리키는 경우 — rename 매핑은
  파일 단위라 폴더 링크는 pass 1 에 안 걸린다. 이동한 폴더명으로 grep 해서 수동 수정.
- gitignore 된 파일(추적 안 됨)은 rename 매핑에 안 뜬다 — 파일시스템으로 옮겼다면
  참조도 손으로.
- 리포 밖 참조(세션 메모리, 에이전트 메모리)는 스캔 범위 밖 — 이동한 경로명으로
  별도 grep.

## 왜 이 순서인가

2026-08-13 StarDiver 재편 실측: 705개 md, 이동 106건, 링크 재계산 265건,
**신규 파손 0**. baseline 을 먼저 뜨지 않으면 "원래 썩어 있던 링크" 와 "내가
깨뜨린 링크" 를 구분할 수 없어서, 게이트가 영원히 빨간불이거나(전량 수리 강요)
전부 통과시키거나(파손 은폐) 둘 중 하나가 된다.

## 다음 단계 (recommended next)

PASS 후: ① 커밋 (이동 + 링크 재계산을 한 커밋으로 — 되돌리기 단위 보존)
② 프로젝트 문서 색인(문서 지도·AGENTS.md 참고 문서 절)이 있으면 같은 커밋에서 갱신
③ 리포 밖 참조(세션 메모리 등)를 이동 경로명으로 grep 해 별도 갱신.
FAIL 후: 출력된 신규 파손 목록만 수리하고 3) 만 재실행 — baseline 을 다시 뜨지
말 것 (다시 뜨면 방금 만든 파손이 baseline 에 흡수돼 게이트가 무력화된다).
