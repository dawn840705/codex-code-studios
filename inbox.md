# Plugin improvement inbox

다른 프로젝트에서 확인한 재사용 가능한 노하우를 플러그인에 반영하기 전 잠시 모아 두는 큐다. 이 파일은 정본이 아니다.

항목에는 날짜·출처 프로젝트·검증 근거·다른 프로젝트에도 적용할 제안만 적는다. 제품 고유 수치, 비밀정보, 개인 절대 경로는 넣지 않는다.

```markdown
## YYYY-MM-DD — 제목

- 출처: 프로젝트와 상대 경로 또는 커밋
- 근거: 실제로 확인한 실패·수리·검증
- 제안: 바꿀 공통 행동 또는 절차
```

처리할 때는 [공통 방침 갱신 절차](docs/policy-updates.md)에 따라 기존 규칙·스킬·템플릿에 반영하고, 검증 후 이 파일의 해당 항목을 지운다. 상세 기록은 출처 프로젝트에 남긴다.

## 2026-10-07 — GPT Bridge로 ChatGPT와 로컬 코드 연결 활용 후보

- 출처: StarDiver 사장님 직접 요청 — 쇼츠 요약을 검토한 뒤 이 방식을 Code Studios 인박스에 남기라고 지시. 상세 검토 = [StarDiver 공유 기록 · 07f649b9c](https://github.com/dawn840705/StarDiver/blob/07f649b9ca8d899ea17b357a442ada358c3a1083/Documents/Shared-Knowledge/Facts-And-References.md). 해당 파일의 «GPT Bridge 활용 검토» 항목 참조.
- 전달받은 방식: VS Code 로컬 서버 → OpenAI 공식 터널 → ChatGPT/Astra가 작업 폴더 코드를 읽고 오류 원인·수정안 제안 → 작업자 검토 후 수동 저장. 영상 URL·GPT Bridge 저장소는 미제공이어서 특정 도구의 동작은 미확인.
- 확인 근거: [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)은 로컬/비공개 MCP 서버 연결을 지원한다. [Pricing](https://learn.chatgpt.com/docs/pricing)은 **ChatGPT Work와 Codex의 한도 공유**를 명시한다. [플러그인 안내](https://learn.chatgpt.com/docs/migrate-custom-gpts)는 일반 Chat에서도 설정에 따라 플러그인을 사용할 수 있다고 설명하지만, 개인 Pro 계정의 Chat+Astra+로컬 MCP가 Codex와 별도 한도를 쓴다는 주장은 확인되지 않았다. 설치·터널 생성·API 호출 시험은 아직 하지 않았다.
- 제안: 범용 오류 분석·코드 리뷰·작은 패치 초안 경로로 검토한다. 읽기 전용 검색·파일 일부 읽기·diff·기존 컴파일 로그 제공부터 시작하고, 수정안은 격리된 패치로 보관한 뒤 기존 실행 담당이 검토·적용·검증한다. 수동 저장은 선택 가능한 모드로 두고 사용자의 반복 작업을 필수로 만들지 않는다. 실제 프로젝트 계약의 경로 소유·실데이터 보호 규칙을 따른다.
- 검증 조건: 정확한 GPT Bridge 배포물과 권한을 먼저 확인한다. 샘플 파일 하나로 Chat/Work 구분·모델·시각·사용량 전후·원본 SHA 불변·패치 정확도·왕복 시간을 기록한다. 반올림된 사용량이 한 번 그대로인 것만으로 한도 분리를 주장하지 않는다. 인증 파일·구매 원본·캐시·실사용 저장 데이터를 제공하지 않으며, 비공개 터널을 로컬 추론으로 오해하지 않는다. 터널과 모델 호출 비용은 따로 확인하고 API 모델 호출을 구독 내 무료 사용으로 가정하지 않는다.
- 상태: **대기 — 활용 후보만 접수. 별도 한도·특정 도구 실측 후 채택 여부 판단.**
