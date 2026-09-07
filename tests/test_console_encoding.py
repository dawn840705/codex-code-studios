# -*- coding: utf-8 -*-
"""없던 층 — 플러그인 CLI 를 적대적 콘솔 인코딩으로 실제 실행하고 종료 코드를 본다.

**이 파일이 존재하는 이유가 버그 자체보다 중요하다.**

`CLAUDE.md § Deterministic gates` 는 «종료 코드가 판정이다» 라고 못박는다. 그런데
Windows 한국어 콘솔(cp949)에서 게이트가 리포트의 em-dash 를 인코딩하지 못해
UnicodeEncodeError 로 죽으면 그 죽음이 `exit 1` 로 나오고, 규칙대로 종료 코드를
믿은 호출자는 **통과한 작업을 FAIL 로 읽는다.**

기존 테스트는 이걸 못 잡았다. 검사 대상 스크립트를 `import` 해서 함수를 직접
불렀기 때문이다 — **`import` 경로에는 콘솔 인코딩이라는 것이 존재하지 않는다.**
그래서 `verify_trajectory.py` 가 CLI 로는 exit 1 로 죽는 순간에도 스위트는
초록이었다. 스크립트에 한 줄씩 넣는 것은 증상 처치고, 재발을 막는 것은 이 층이다.

설계상 지키는 두 가지:

1. **목록을 하드코딩하지 않는다.** `scripts/*.py` 를 훑어 진입점을 찾고, 시나리오가
   없는 진입점은 그 자체로 실패시킨다. 하드코딩하면 다음에 추가되는 스크립트를
   그대로 놓친다.
2. **`--help` 만 때리지 않는다.** `verify_gates`·`verify_trajectory` 는 `--help` 는
   멀쩡하고 **정상 실행 경로에서** 죽었다. 그래서 모든 진입점에 실제 실행
   시나리오를 하나 이상 요구한다.

판정 기준도 두 가지다 — 죽지 않는 것(`UnicodeEncodeError` 부재)만으로는 부족하고,
**종료 코드가 인코딩과 무관해야** 한다. 그게 이 버그가 깬 계약이다.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_SCRIPTS = os.path.join(_ROOT, "scripts")

# 적대적 인코딩. cp949 = 한국어 Windows 콘솔(실제 사고 현장),
# ascii = 로케일 일반 — 이 둘을 통과하면 나머지 좁은 로케일도 사실상 덮인다.
HOSTILE = ("cp949", "ascii")
# 비교 기준. 「인코딩과 무관해야 한다」는 계약의 기준선.
REFERENCE = "utf-8"


# ---------------------------------------------------------------------------
# 진입점 발견 — 목록 하드코딩 금지
# ---------------------------------------------------------------------------

def entry_points() -> list[str]:
    """`scripts/*.py` 중 CLI 진입점인 파일명. 라이브러리 모듈은 제외한다."""
    found = []
    for path in sorted(glob.glob(os.path.join(_SCRIPTS, "*.py"))):
        with open(path, encoding="utf-8") as f:
            if '__name__ == "__main__"' in f.read():
                found.append(os.path.basename(path))
    return found


# ---------------------------------------------------------------------------
# 실제 실행 시나리오 — 픽스처 빌더는 (args, cwd) 를 돌려준다
# ---------------------------------------------------------------------------

def _humanize_pair(tmp):
    before = os.path.join(tmp, "01_input.txt")
    after = os.path.join(tmp, "final.md")
    with open(before, "w", encoding="utf-8") as f:
        f.write("원문입니다. 이것은 게이트를 실제로 태우기 위한 문장이며, "
                "충분히 길게 써서 지표가 계산되도록 합니다. 그리고 한 문장 더.\n")
    with open(after, "w", encoding="utf-8") as f:
        f.write("원문이다. 이건 게이트를 실제로 태우려고 쓴 문장인데, "
                "지표가 나오도록 길게 썼다. 한 문장 더 붙인다.\n")
    return before, after


def _sc_verify_gates(tmp):
    before, after = _humanize_pair(tmp)
    return ["--before", before, "--after", after], tmp


def _sc_verify_change_rate(tmp):
    before, after = _humanize_pair(tmp)
    return ["--before", before, "--after", after], tmp


def _sc_check_phase_ambiguous(tmp):
    # game·product 마커가 둘 다 있으면 「CANNOT JUDGE: ... — 」 경로를 탄다.
    os.makedirs(os.path.join(tmp, "design", "gdd"), exist_ok=True)
    os.makedirs(os.path.join(tmp, "product", "prd"), exist_ok=True)
    return ["--root", tmp], tmp


def _sc_check_phase_json(tmp):
    # 공통 게이트 리포트(gate_report) 봉투. reason 에 em-dash 가 들어간다.
    return ["--root", tmp, "--json"], tmp


def _sc_lint_skills(tmp):
    # 규정 위반 스킬 하나. 린터가 지적 문구에 em-dash 를 찍는 그 경로다.
    d = os.path.join(tmp, "skills", "broken")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("---\nname: broken\ndescription: d\n---\n\nbody\n")
    return [os.path.join(tmp, "skills")], tmp


def _sc_doc_relink(tmp):
    docs = os.path.join(tmp, "Documents")
    os.makedirs(docs, exist_ok=True)
    with open(os.path.join(docs, "a.md"), "w", encoding="utf-8") as f:
        f.write("# 문서\n\n[깨진 링크](./nope.md)\n")
    return ["check", tmp, "--docs", "Documents"], tmp


def _sc_removebg(tmp):
    # estimate = 「호출 없이 크레딧 추정」. 유료 API 를 때리지 않는 경로만 쓴다.
    png = os.path.join(tmp, "x.png")
    with open(png, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
    return ["estimate", png], tmp


def _sc_reasoning_effort(tmp):
    # Actual observation, no model invocation. Prompt is deliberately Korean;
    # privacy hashing keeps nondeterministic record metadata ASCII-only.
    task = os.path.join(tmp, "task.json")
    with open(task, "w", encoding="utf-8") as stream:
        json.dump({"task_id": "console-case", "prompt": "저장 고쳐",
                   "model": "gpt-5.5"}, stream, ensure_ascii=False)
    return ["observe", "--task", task, "--root", tmp], tmp


def _sc_prepare_monolith(tmp):
    # --run-dir 모드. --text 모드는 저장소 _workspace/ 에 쓰므로 테스트에 부적합.
    run = os.path.join(tmp, "run")
    os.makedirs(run, exist_ok=True)
    with open(os.path.join(run, "01_input.txt"), "w", encoding="utf-8") as f:
        f.write("안녕하세요. 이것은 테스트 문장입니다. 조금 더 길게 써 봅니다.\n")
    return ["--run-dir", run], tmp


def _sc_reassemble(tmp):
    run = os.path.join(tmp, "run")
    os.makedirs(run, exist_ok=True)
    text = "안녕하세요. 이것은 청킹 재조립을 실제로 태우기 위한 원문입니다.\n"
    with open(os.path.join(run, "01_input.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    # 원문 대비 크게 줄어든 윤문 → 「유실 의심」 한국어 경고 경로를 태운다.
    with open(os.path.join(run, "chunk_0.md"), "w", encoding="utf-8") as f:
        f.write("짧다.\n")
    manifest = {
        "source_file": "01_input.txt",
        "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "chunks": [{
            "index": 0, "start": 0, "end": len(text),
            "passthrough": False, "rewritten_file": "chunk_0.md",
        }],
    }
    with open(os.path.join(run, "chunk_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False)
    return ["--run-dir", run], tmp


def _sc_repo(*args):
    """저장소 자신을 대상으로 도는 게이트 — cwd 가 저장소여야 한다."""
    def build(tmp):
        return list(args), _ROOT
    return build


# 진입점 → 실제 실행 시나리오. `--help` 는 아래에서 전 진입점에 자동으로 덧붙는다.
SCENARIOS = {
    "build_diagnosis_rules.py": [("check", _sc_repo("--check"))],
    "build_quick_rules.py": [("check", _sc_repo("--check"))],
    "check_phase.py": [
        ("ambiguous-track", _sc_check_phase_ambiguous),
        ("gate-report-json", _sc_check_phase_json),
    ],
    "doc_relink.py": [("check-broken-links", _sc_doc_relink)],
    "lint_skills.py": [("non-compliant-skill", _sc_lint_skills)],
    "prepare_monolith_input.py": [("run-dir", _sc_prepare_monolith)],
    "reassemble_chunks.py": [("shrink-warning", _sc_reassemble)],
    "removebg.py": [("estimate-dry-run", _sc_removebg)],
    "reasoning_effort.py": [("observe-no-inference", _sc_reasoning_effort)],
    "verify_change_rate.py": [("real-pair", _sc_verify_change_rate)],
    "verify_gates.py": [("real-pair", _sc_verify_gates)],
    "verify_policy.py": [("self-test", _sc_repo("--self-test"))],
    "verify_trajectory.py": [("golden-compare", _sc_repo())],
}


# ---------------------------------------------------------------------------
# 실행
# ---------------------------------------------------------------------------

def _run(script: str, args: list[str], cwd: str, encoding: str):
    """CLI 를 subprocess 로 실행한다. **바이트로 받는다** — 디코딩 자체가
    이 층이 검사하려는 실패 지점이라, 하네스가 먼저 죽으면 안 된다."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = encoding
    return subprocess.run(
        [sys.executable, os.path.join(_SCRIPTS, script), *args],
        cwd=cwd, env=env, capture_output=True, timeout=180,
    )


def _cases():
    for script in entry_points():
        yield pytest.param(script, "--help", None, id=f"{script}::--help")
        for label, build in SCENARIOS.get(script, []):
            yield pytest.param(script, label, build, id=f"{script}::{label}")


# ---------------------------------------------------------------------------
# 테스트
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("script", entry_points())
def test_every_entry_point_has_a_real_run_scenario(script):
    """새 스크립트가 `--help` 만 검사받고 빠져나가지 못하게 하는 잠금장치.

    `verify_gates`·`verify_trajectory` 는 `--help` 는 멀쩡했고 정상 실행
    경로에서 죽었다. 시나리오 없는 진입점은 그 사고를 그대로 반복한다.
    """
    assert SCENARIOS.get(script), (
        f"{script} 에 실제 실행 시나리오가 없다. tests/test_console_encoding.py 의 "
        f"SCENARIOS 에 추가할 것 — `--help` 통과는 CLI 가 안전하다는 증거가 아니다."
    )


@pytest.mark.parametrize("script,label,build", list(_cases()))
@pytest.mark.parametrize("encoding", HOSTILE)
def test_cli_does_not_die_on_hostile_console_encoding(
    script, label, build, encoding, tmp_path
):
    """적대적 콘솔에서 UnicodeEncodeError 로 죽지 않는다 (합격 기준 §5-1)."""
    args, cwd = ([label], str(tmp_path)) if build is None else build(str(tmp_path))
    proc = _run(script, args, cwd, encoding)
    assert b"UnicodeEncodeError" not in proc.stderr, (
        f"{script} [{label}] 이 PYTHONIOENCODING={encoding} 에서 인코딩 중 죽었다 "
        f"(exit {proc.returncode}). 게이트의 판정이 콘솔 코드페이지에 좌우된다.\n"
        f"--- stderr ---\n{proc.stderr.decode('utf-8', 'replace')}"
    )


@pytest.mark.parametrize("script,label,build", list(_cases()))
@pytest.mark.parametrize("encoding", HOSTILE)
def test_exit_code_is_independent_of_console_encoding(
    script, label, build, encoding, tmp_path
):
    """종료 코드가 인코딩과 무관하다 (합격 기준 §5-2).

    죽지 않는 것만으로는 부족하다. 이 플러그인의 계약은 «종료 코드가 판정이다»
    이므로, 같은 입력이면 콘솔이 무엇이든 같은 판정이 나와야 한다.
    """
    ref_dir = tmp_path / "ref"
    hostile_dir = tmp_path / "hostile"
    ref_dir.mkdir()
    hostile_dir.mkdir()

    if build is None:
        ref = _run(script, [label], str(ref_dir), REFERENCE)
        hostile = _run(script, [label], str(hostile_dir), encoding)
    else:
        a, cwd_a = build(str(ref_dir))
        b, cwd_b = build(str(hostile_dir))
        ref = _run(script, a, cwd_a, REFERENCE)
        hostile = _run(script, b, cwd_b, encoding)

    assert hostile.returncode == ref.returncode, (
        f"{script} [{label}] 의 판정이 콘솔 인코딩에 따라 갈린다: "
        f"{REFERENCE}→exit {ref.returncode}, {encoding}→exit {hostile.returncode}.\n"
        f"--- {encoding} stderr ---\n{hostile.stderr.decode('utf-8', 'replace')}"
    )


@pytest.mark.parametrize("script", entry_points())
def test_non_ascii_output_survives_every_encoding(script, tmp_path):
    """비ASCII 출력이 인코딩과 무관하게 **글자 그대로** 살아 있다 (합격 기준 §5-3).

    앞의 두 테스트만으로는 부족하다. 비ASCII 를 전부 ASCII 로 치환하거나
    `errors="replace"` 가 실제로 발동해 글자가 「?」로 뭉개져도 종료 코드는
    멀쩡해지므로 둘 다 초록이 된다. 그건 수리가 아니다 — 게이트 리포트가
    한국어인 것은 사양이고, 글자를 잃으면 사람이 판정을 못 읽는다.

    그래서 두 가지를 건다.

    - 진입점마다 비ASCII 를 내보내는 경로가 **적어도 하나는** 있어야 한다.
      (§2 의 13개 스크립트 전부가 여기 해당한다. 전량 ASCII 화 우회 차단)
    - 그 경로의 출력은 적대적 인코딩에서도 utf-8 콘솔과 **바이트까지 같아야**
      한다. U+FFFD 하나만 섞여도 실패다.
    """
    cases = [("--help", None)] + list(SCENARIOS.get(script, []))
    carriers = []

    for i, (label, build) in enumerate(cases):
        work = tmp_path / f"case{i}"
        work.mkdir()
        args, cwd = ([label], str(work)) if build is None else build(str(work))

        ref = _run(script, args, cwd, REFERENCE)
        blob = ref.stdout + ref.stderr
        try:
            expected = blob.decode("utf-8")
        except UnicodeDecodeError as exc:  # pragma: no cover - 회귀 시에만
            pytest.fail(f"{script} [{label}] 의 utf-8 출력이 utf-8 로 디코딩되지 않는다: {exc}")

        if expected.isascii():
            continue  # 이 경로는 원래 ASCII 만 낸다 — 비교 대상이 아니다
        carriers.append(label)

        # 같은 작업 디렉토리에 그대로 다시 태운다. 인코딩 말고는 변수가 없어야 한다.
        for encoding in HOSTILE:
            got = (lambda p: p.stdout + p.stderr)(_run(script, args, cwd, encoding))
            actual = got.decode("utf-8", "replace")
            assert "�" not in actual, (
                f"{script} [{label}] 의 출력이 PYTHONIOENCODING={encoding} 에서 "
                f"깨졌다 (U+FFFD). 죽지는 않았지만 사람이 판정을 못 읽는다.\n"
                f"--- output ---\n{actual[:500]}"
            )
            assert actual == expected, (
                f"{script} [{label}] 의 출력이 콘솔 인코딩에 따라 달라진다 "
                f"({REFERENCE} vs {encoding}).\n"
                f"--- {REFERENCE} ---\n{expected[:400]}\n"
                f"--- {encoding} ---\n{actual[:400]}"
            )

    assert carriers, (
        f"{script} 가 어느 경로에서도 비ASCII 를 내보내지 않는다. 인코딩 버그를 "
        f"「비ASCII 를 지워서」 해결한 것이라면 그건 수리가 아니다 — 출력이 "
        f"한국어인 것은 사양이다. 정말 ASCII 전용 스크립트라면 이 단언을 "
        f"의도적으로 완화할 것."
    )


# ---------------------------------------------------------------------------
# 반대 방향 — 하네스가 자식 출력을 디코딩하다 죽는 실패 (발주 §2-b)
# ---------------------------------------------------------------------------

def test_every_text_mode_subprocess_pins_utf8():
    """`tests/` 와 `scripts/` 의 텍스트 모드 subprocess 호출이 utf-8 을 명시했는지.

    스크립트는 출력을 **인코딩**하다 죽고, 하네스는 자식 출력을 **디코딩**하다
    죽는다. 뿌리는 하나지만 수리는 별개다 — `PYTHONIOENCODING=utf-8` 은
    `sys.stdout.encoding` 만 바꾸고 `subprocess(text=True)` 가 쓰는
    `locale.getencoding()` 에는 영향이 없다. 그래서 §4-1 을 다 고쳐도
    한국어 Windows 에서 훅 테스트 21건은 그대로 죽어 있었다.

    `scripts/` 까지 훑는 이유 — 같은 결함이 배포 코드에도 있었다.
    `verify_policy.py` 는 `git diff` 를 locale 인코딩으로 읽다가 리더 스레드가
    죽어 `stdout` 이 `None` 이 됐고, 게이트는 판정 대신 AttributeError 로
    무너졌다. 한국어가 섞인 diff 에서만 터지므로 작업 트리가 깨끗한 동안에는
    보이지 않는다 — 즉 **커밋할 내용이 있을 때만** 게이트가 무너졌다.

    이 단언이 없으면 다음에 `text=True` 만 붙이는 편집 한 번으로 재발한다.
    """
    offenders = []
    scanned = (glob.glob(os.path.join(_HERE, "*.py"))
               + glob.glob(os.path.join(_SCRIPTS, "*.py")))
    for path in sorted(scanned):
        with open(path, encoding="utf-8") as f:
            src = f.read()
        for call in re.finditer(r"subprocess\.run\(", src):
            depth, i = 0, call.end() - 1
            while i < len(src):
                if src[i] == "(":
                    depth += 1
                elif src[i] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            body = src[call.end():i]
            if "text=True" in body and "encoding=" not in body:
                line = src[:call.start()].count("\n") + 1
                where = os.path.relpath(path, _ROOT).replace(os.sep, "/")
                offenders.append(f"{where}:{line}")

    assert not offenders, (
        "text=True 만 주고 encoding= 을 안 준 subprocess 호출: "
        + ", ".join(offenders)
        + ". text=True 는 locale.getencoding() 을 타므로 한국어 Windows 에서 "
        "자식의 UTF-8 출력(⚠️ 등)을 디코딩하다 죽는다. encoding=\"utf-8\" 을 명시할 것."
    )
