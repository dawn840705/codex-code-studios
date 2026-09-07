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
- 생성한 EventSystem에서 선택이 바뀌었다는 사실만으로 제품 경로를 검증하지 않는다. 제품이 읽는 `EventSystem.current`와 fixture 대상이 같은지, 그 current의 실제 선택이 기대값인지 단언한다. 사용 중인 패키지의 등록/해제 경로를 확인하고 자동 호출 여부와 겹쳐 이중 등록하지 않는다.
- 전역 property setter가 `null`이나 임의 객체를 허용한다고 가정하지 않는다. 특히 `EventSystem.current` setter는 등록을 대체하지 않는다. 기존 시스템·선택·singleton·저장 경로를 보존하고 `finally`/teardown에서 소유 객체만 해제·제거한 뒤 원상복원한다.
- 러너가 저장된 씬을 요구해도 사용자 씬을 저장하여 제약을 우회하지 않는다. 필요한 경우 고유 경로의 **임시 scene asset을 Additive로 격리**하고 활성 씬·열린 씬·사용자 dirty 상태를 보존한다. 시험 뒤 임시 씬만 닫고 생성한 asset/meta만 제거하며 기존 상태가 유지됐는지 검증한다. 보호 상태를 유지할 수 없는 러너라면 중단 사유를 기록한다.
- reflection의 `MethodInfo.Invoke`에도 선택한 overload의 인자 슬롯을 모두 전달한다. C# optional parameter의 호출부 생략이 reflection에서도 자동 적용된다고 가정하지 말고 명시적 기본값 또는 해당 API가 지원하는 missing-value 방식을 사용한다.

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
