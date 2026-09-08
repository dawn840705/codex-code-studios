# Unity MCP Workflow Patterns

> **컨텍스트**: Codex + CoplayDev/unity-mcp (HTTP localhost:8080) 통한 Unity Editor 자동화 패턴. 씬 / GameObject / 컴포넌트 / Build Settings 까지 자동.

---

## § 1 — MCP 도구 선택 기준

| 도구 | 사용 시점 |
|------|----------|
| `manage_scene` (create/load/save/get_hierarchy) | 씬 단위 작업 |
| `manage_gameobject` (create/modify/delete) | 단일 GameObject 작업 |
| `manage_components` (add/remove/set_property) | 컴포넌트 단위 작업 |
| `manage_prefabs` (modify_contents/open_prefab_stage) | prefab 편집 (Headless / Interactive 모드) |
| `find_gameobjects` | name/tag/component 검색 (instance ID 반환) |
| `execute_code` | 위 도구로 불가능한 작업 (reflection / sub-asset 매핑 / 복잡 로직) |
| `batch_execute` | **N 명령 1회 호출 — 성능 10~100x 향상** |

---

## § 2 — 핵심 패턴

### 2.1 MCP 연결을 먼저 확인

Codex에 MCP 서버가 등록되어 있고 Unity Editor가 서버를 제공 중인지 먼저 확인한다:

```bash
codex mcp list
codex mcp get unityMCP
```

연결된 태스크에서 Unity MCP 도구가 보이지 않으면 Unity Editor와 서버 상태를
확인한 뒤 Codex 태스크를 다시 시작한다.

### 2.2 batch_execute — 다수 명령 1회

10+ GameObject 생성 / 컴포넌트 set / 씬 save 등 N 명령 *1 batch* 으로 처리:

```json
{
  "commands": [
    {"tool": "manage_gameobject", "params": {"action": "create", ...}},
    {"tool": "manage_components", "params": {"action": "set_property", ...}},
    {"tool": "manage_scene", "params": {"action": "save"}}
  ]
}
```

기본 max 25 명령 / hard max 100. UI widget 일괄 생성 시 *필수* 사용 (매 명령 latency 합산 시 분 단위 지연).

### 2.3 instance ID vs path

scene GameObject 의 `target` reference:
- **instance ID** (int) — 정확. recompile / domain reload 시 변경 가능 → 작업 직후 사용.
- **path** (string) — Canvas/MainPanel/Button 형식. 비활성 GameObject 도 `find_gameobjects` + `include_inactive=true` 으로 검색.

권장:
1. `find_gameobjects` → instance ID 받기
2. batch_execute 안 같은 ID 재사용
3. recompile 후엔 다시 find

### 2.4 execute_code — reflection / sub-asset 매핑

MCP 의 standard tool 으로 불가능한 작업:
- SerializedField nested array set (예: `SlotEntry[] slotEntries`)
- InputActionReference sub-asset 매핑 (InputAction.actionMap.actions)
- Selectable.navigation Explicit set (struct)
- PrefabUtility.LoadPrefabContents 으로 prefab 직접 편집

```csharp
// 예: InputActionReference 매핑
var subAssets = UnityEditor.AssetDatabase.LoadAllAssetsAtPath("Assets/.../X.inputactions");
foreach (var sa in subAssets) {
    if (sa is InputActionReference iar && iar.name == "UI/Navigate")
        module.move = iar;
}
```

execute_code = method body 형식. `using` directive X (전체 namespace 사용).

---

## § 3 — 회귀 사고 패턴

### 3.1 set_property nested array
`manage_components.set_property` 의 nested SerializedField 배열 set 시 *outer 배열 entry* 만 생성되고 *inner ref 모두 null*. `execute_code` 으로 직접 set 권장.

### 3.2 Component 매핑 자동 reset
Button.Transition 변경 (예: Sprite Swap → Color Tint) 시 Unity 가 targetGraphic 자동 reset → *기본 첫 Image* 으로 fallback. 사장님 변경 후 *컴포넌트 ref 재검증* 필수.

### 3.3 Play mode 중 EditorSceneManager
Play 중 `EditorSceneManager.OpenScene` 호출 시 *InvalidOperationException*. 사장님께 Play 종료 안내.

### 3.4 MCP session "Session not found"
MCP server stale 또는 Unity Editor 미활성. Unity Editor를 활성화하고
`codex mcp get unityMCP`로 등록 상태를 확인한 뒤 태스크 연결을 새로 시작한다.

### 3.5 Static batching — Transform과 실제 화면을 함께 검증

이 절과 다음 절은 제어 도구와 무관한 Unity 검증 절차다. 프로젝트 실기에서 Transform만 바뀌고 표시 위치가 유지된 사례, EditMode fixture의 생명주기·등록 누락을 수리한 결과를 반영한다. 제품별 증거·수치·경로는 해당 프로젝트에 보존한다.

- Play의 static-batched renderer는 자식 Transform 변경만으로 화면이 기대대로 이동하지 않을 수 있다. `Transform` 좌표만 읽고 이동·접지·크기 수리를 통과시키지 않는다. 배칭 여부, `Renderer.bounds`, 실제 카메라 캡처를 함께 비교한다.
- 원본 prefab을 격리해 배칭 전 상태로 조사한 결과는 **원인 진단**이다. 제품 씬에서 scene override·배칭·실제 카메라가 적용된 상태의 검증과 구분한다. 진단을 위해 원본 자산의 static 플래그나 사용자 씬을 임의 저장하지 않는다.
- 제품 수정은 승인된 저장 대상에만 반영하고, 재로드 후 실제 표시·bounds·캡처를 다시 확인한다. 격리 진단의 성공을 제품 재로드 검증으로 대신하지 않는다.

### 3.6 EditMode fixture — 생명주기·전역 상태·씬 격리

- 일반 `MonoBehaviour`의 EditMode 생성/활성화/파괴가 Play와 같은 `Awake`·`OnEnable`·`OnDisable`·`OnDestroy` 전달을 보장한다고 가정하지 않는다. 콜백 계약 시험은 필요한 실제 메서드를 명시 호출하고 구독 해제·재활성화 중복을 단언한다. 자동 전달과 실제 입력은 별도 Play 시험으로 확인한다.
- 런타임 `AddComponent`의 필수 설정을 Editor `Reset`에 의존하지 않는다. 설치 패키지의 필드 초기값과 `Reset`을 비교하고, 신규 컴포넌트에 필요한 값을 명시하되 기존 저작 컴포넌트는 보존한다. EditMode에서는 `Reset`이 결함을 숨길 수 있으므로 PlayMode의 실제 제품 생성 경로에서 양성 출력을 먼저 단언한 뒤 0·중간 배율·진행 중 종료를 검사한다. 발신·수신 초기화 누락으로 모든 배율에서 카메라 출력이 0이었던 결함과 수리 후 PlayMode 회귀 통과를 근거로 하며, 신호 계산 검증과 실제 렌더 검증은 구분한다.
- 생성한 EventSystem에서 선택이 바뀌었다는 사실만으로 제품 경로를 검증하지 않는다. 제품이 읽는 `EventSystem.current`와 fixture 대상이 같은지, 그 current의 실제 선택이 기대값인지 단언한다. 사용 중인 패키지의 등록/해제 경로를 확인하고 자동 호출 여부와 겹쳐 이중 등록하지 않는다.
- 전역 property setter가 `null`이나 임의 객체를 허용한다고 가정하지 않는다. 특히 `EventSystem.current` setter는 등록을 대체하지 않는다. 기존 시스템·선택·singleton·저장 경로를 보존하고 `finally`/teardown에서 소유 객체만 해제·제거한 뒤 원상복원한다.
- 러너가 저장된 씬을 요구해도 사용자 씬을 저장하여 제약을 우회하지 않는다. 필요한 경우 고유 경로의 **임시 scene asset을 Additive로 격리**하고 활성 씬·열린 씬·사용자 dirty 상태를 보존한다. 시험 뒤 임시 씬만 닫고 생성한 asset/meta만 제거하며 기존 상태가 유지됐는지 검증한다. 보호 상태를 유지할 수 없는 러너라면 중단 사유를 기록한다.
- reflection의 `MethodInfo.Invoke`에도 선택한 overload의 인자 슬롯을 모두 전달한다. C# optional parameter의 호출부 생략이 reflection에서도 자동 적용된다고 가정하지 말고 명시적 기본값 또는 해당 API가 지원하는 missing-value 방식을 사용한다.

### 3.7 비동기 셰이더 — 사용 중인 material/pass의 완료 확인

- 비동기 셰이더 컴파일의 cyan 중간 화면을 재질색 불합격으로 판정하지 않는다. `ShaderUtil.anythingCompiling == false`여도 해당 material/pass의 `ShaderUtil.IsPassCompiled(material, passIndex)`는 false일 수 있다. 실제 셰이더·사용 pass와 그 완료 상태를 확인한다.
- 원본 재질 속성·keyword·texture 참조를 먼저 기록·보존한다. 사용 pass가 0임을 확인한 경우 `ShaderUtil.CompilePass(material, 0, true)`로 해당 pass를 컴파일하고 `IsPassCompiled` 및 셰이더 메시지를 다시 확인한다. 다른 pass를 쓰면 실제 인덱스를 사용하며, 하나의 pass 완료를 전체 셰이더 완료로 확대하지 않는다.
- 실제 pass 완료 후 원래 재질 조건으로 다시 캡처해 색을 판정한다. 컴파일 전 cyan을 없애려고 팔레트·texture·keyword를 연쇄 변경하지 않는다. 근거는 원본 값을 유지한 채 사용 pass를 컴파일하자 cyan이 해소된 실기 결과이며, 상세 증거는 원 프로젝트에 보존한다.

### 3.8 저장 fixture — 파일 복구보다 쓰기 경로 격리 우선

- 고정된 큰 테스트 슬롯 번호도 `Application.persistentDataPath` 안에서는 사용자 파일과 충돌할 수 있다. 저장 두 번으로 기존 `.bak`가 덮이고 본문 파일만 정리된 실제 사례를 반영한다. 사용자 파일 snapshot·사후 restore만으로 안전하다고 간주하지 않는다.
- 실행마다 고유 임시 디렉터리를 만들고, 첫 저장·저장 객체 활성화 전에 프로젝트의 경로 override seam(예: `_slotDirectoryOverride`)을 적용한다. `GetSlotPath` 등 **제품이 실제 사용하는 경로 계산 결과**를 절대 경로로 확인해 그 임시 디렉터리 내부임을 단언한다. 본문뿐 아니라 `.bak`·`.tmp` 등 모든 sidecar의 쓰기·읽기·정리를 격리하며, 반복 저장 시험은 백업 내용도 검사한다.
- 기존 singleton·경로 override를 보존하고 `finally`/teardown에서 시험 객체의 종료 처리를 격리 경로 안에서 마친 뒤 원상복원한다. 자신이 만든 임시 경로임을 재검사한 후 그 범위만 회수한다. 수리 fixture 재실행과 실제 사용자 파일의 전후 존재 여부·SHA 비교가 모두 맞아야 격리 수리를 통과시킨다. 전용 재실행 성공·사용자 파일 해시 불변으로 검증한 절차이며, 파일 수·슬롯 번호·복구 경로는 원 프로젝트에만 기록한다.

### 3.9 Input System — 입력 주입 경로와 fixture update 격리

- **버전 한정 관측**: Unity `6000.3.23f1` / Input System `1.20.0`에서 Hera의 `onBeforeUpdate` 콜백이 `InputState.Change`로 버튼 상태를 즉시 바꾸는 경로를 조사했다. 그 입력으로 UI action map을 전환하면 state monitor 알림 도중 monitor가 즉시 제거되어 `DynamicBitfield.ClearBit` assertion으로 이어질 수 있는 재진입 경로가 설치 소스와 실제 스택에서 확인됐다. 모든 Hera 입력이나 정상 장치 이벤트에 같은 결함이 있다고 일반화하지 않는다.
- 입력 자동화 중 assertion이 발생하면 원본 로그·주입 API·update 단계·action map을 먼저 보존한다. 제품 가드를 약화하거나 예외를 숨기지 말고, `QueueStateEvent` / `QueueDeltaStateEvent`로 이벤트를 큐에 넣어 정상 Input System update에서 소비하는 경로로 같은 시나리오를 재검증한다. press·release·재입력과 모달 진입/복귀를 함께 확인한다. 직접 메서드 호출의 성공은 실제 입력 경로의 대체 증거가 아니다.
- UI 회귀는 제품이 실제 사용하는 입력 드라이버의 분기·전달 경로를 포함한다. 개별 위젯의 `OnMove` 성공만으로 공용 내비게이션의 슬라이더 조작을 통과시키지 않는다. 실제 드라이버를 거쳐 값 변경·경계값·축에 따른 포커스 이동·중복 이벤트를 검사하고 queued 입력으로 제품 경로를 재확인한다. 공용 드라이버가 슬라이더 값 조작을 포커스 이동으로 처리하던 결함을 검출·수리한 절차이며, 직접 드라이버 호출과 장치 입력 증거는 따로 기록한다.
- 제품 동작 결과와 도구/패키지 assertion을 별도로 기록한다. 동작이 맞아도 assertion이 남은 실행을 콘솔 무오류로 처리하지 않는다. 로그 보존 후 새 검증 구간을 정해 queued 입력으로 재실행하고, 동작·콘솔 결과를 각각 확인한다. 이 절의 절차는 전용 회귀와 제품의 정상 진입 경로에서 queued 입력 재검증으로 확인했으며 상세 증거는 원 프로젝트에 둔다.
- 같은 설치 버전의 `InputTestFixture`는 `UnityTest`에서 press/release helper를 큐에만 넣을 수 있다. `ProcessEventsManually` 시험은 필요한 입력 경계에서 명시적으로 `InputSystem.Update()`하고 실제 버튼 값·action phase·reader 상태·update count를 단언한다. **맵 복귀 후 initial-state check 이전**을 검증하는 구간에는 update나 held 상태 재주입을 넣어 시험하려는 순서를 없애지 않는다.
- Manual 설정 변경이 `ApplySettings`를 거치며 Editor update bit를 다시 켜는지도 설치 소스로 확인한다. 확인된 버전에서는 fixture의 원래 Editor update 차단을 **fixture가 만든 격리 Input System manager에만** 다시 적용해 Editor buffer 전환의 간섭을 막았다. 이를 제품 코드나 원래 manager에 적용하는 공통 처방으로 쓰지 않는다. 내부 필드 접근이 필요하면 설치 버전의 fixture 구현과 일치하는지 확인하고, teardown에서 원래 runtime·manager·장치·설정을 복원하며 수명/복원 단언을 유지한다. 패키지나 설치 캐시는 고치지 않는다.

---

## § 4 — 작업 흐름 (UI 신설 예시)

```
1. `codex mcp get unityMCP` — 서버 등록 및 URL 확인
2. read_console — 컴파일 에러 0 확인
3. manage_scene create + load — 신규 씬
4. batch_execute:
   - Main Camera + EventSystem + Canvas 생성
   - UI widget hierarchy (Panel + Buttons + Texts) 생성
   - RectTransform set + 텍스트 alignment + 컴포넌트 ref
5. find_gameobjects — instance ID 확인
6. manage_components.set_property — Manager Inspector ref 매핑
7. execute_code — nested array / Selectable.navigation Explicit set
8. manage_scene save
9. refresh_unity (compile request)
10. read_console — 에러 검증
```

---

## § 5 — 안티패턴

- ❌ 매 명령 개별 호출 (batch_execute 사용 X) — latency 폭증
- ❌ instance ID 캐싱 후 recompile 거쳐 재사용 — 깨질 수 있음
- ❌ execute_code 안에 `using` directive — codedom 컴파일 실패
- ❌ 승인된 제품 변경의 scene save 누락 — 작업 결과 손실
- ❌ `manage_scene.load`/테스트 러너의 제약을 우회하려고 사용자 unsaved changes 저장 — 소유 변경만 저장하고, 검증은 § 3.6의 격리·복원 경계를 따른다

---

## § 6 — 권장 setup

Codex CLI에서 HTTP MCP 서버를 등록한다:

```bash
codex mcp add unityMCP --url http://localhost:8080
```

등록 결과는 `~/.codex/config.toml`에 저장되며 `codex mcp get unityMCP`로 확인한다.
