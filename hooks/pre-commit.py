"""Validate commit files once in Python instead of spawning grep per section."""
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("post_edit", ROOT / "post-edit.py")
edit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edit)
SECTIONS = ("Overview", "Player Fantasy", "Detailed", "Formulas", "Edge Cases",
            "Dependencies", "Tuning Knobs", "Acceptance Criteria")
HARDCODED = re.compile(r"(damage|health|speed|rate|chance|cost|duration)\s*[:=]\s*[0-9]+")
TODO = re.compile(r"(TODO|FIXME|HACK)[^(]")


def main():
    edit.force_utf8()
    try:
        event = json.loads(edit.runner.read_input(1))
        tool = event.get("tool_input", {})
        command = tool.get("command", tool.get("cmd", ""))
        if not re.search(r"^git\s+commit", command):
            return 0
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "diff",
             "--cached", "--name-only", "-z"], capture_output=True, timeout=3)
        if result.returncode:
            raise ValueError("could not read staged file paths")
        files = [name.decode("utf-8") for name in result.stdout.split(b"\0") if name]
        if not files:
            return 0
        setting, engine, _ = edit.layout_settings()
        asset_roots, _, _ = edit.asset_layout()
        defaults = {"unity": "cs", "godot": "gd cs", "unreal": "cpp h hpp", "gamemaker": "gml"}
        exts = setting("STUDIO_SRC_EXTS", "srcExtensions", defaults.get(
            engine, "gd cs cpp c h hpp rs py js ts tsx jsx go java kt swift"))
        if isinstance(exts, str):
            exts = exts.replace(":", " ").split()
        candidates = ["design/gdd", "Documents", "Docs", "docs/design", "docs/gdd", "product/prd"]
        if engine in ("godot", "gamemaker"):
            candidates = ["design/gdd", "docs/design", "Documents", "product/prd"]
        elif engine not in ("unity", "unreal"):
            candidates = ["design/gdd", "product/prd", "docs/design", "docs/gdd"]
        roots = setting("STUDIO_DESIGN_ROOTS", "designRoots", None)
        if roots is None:
            roots = [r for r in candidates if Path(r).is_dir()] or ["design/gdd"]
        elif isinstance(roots, str):
            roots = roots.split(":")
        if not isinstance(roots, list) or not isinstance(exts, list) \
                or not all(isinstance(v, str) for v in roots + exts):
            raise ValueError("designRoots/srcExtensions must contain strings")
        warnings, hardcoded, todos = [], [], []
        code_count = 0
        for name in files:
            file = Path(name)
            if not file.is_file():
                continue
            design = [r.rstrip("/") for r in roots if r and r.rstrip("/") != "."
                      and name.startswith(r.rstrip("/") + "/") and file.suffix == ".md"]
            asset = any(re.search(r"(?:^|/)" + re.escape(r.rstrip("/")) + "/", name)
                        for r in asset_roots if r) or bool(re.search(r"(?:^|/)assets/data/", name))
            code = file.suffix.lstrip(".") in exts
            # ponytail: source advice scans 200 files; use a full audit for larger commits.
            if code:
                code_count += 1
            if not design and not (asset and file.suffix == ".json") and not (code and code_count <= 200):
                continue
            content = file.read_text(encoding="utf-8")
            if asset and file.suffix == ".json":
                try:
                    json.loads(content)
                except ValueError:
                    print(f"BLOCKED: {name} is not valid JSON", file=sys.stderr)
                    return 2
            present = [section for section in SECTIONS if section.lower() in content.lower()]
            for root in design:
                if root == "design/gdd" or len(present) >= 3:
                    warnings += [f"DESIGN: {name} missing required section: {section}"
                                 for section in SECTIONS if section not in present]
            if code and code_count <= 200:
                if HARDCODED.search(content):
                    hardcoded.append(name)
                if TODO.search(content):
                    todos.append(name)
        for label, hits in (("CODE: may contain hardcoded gameplay values — use data files", hardcoded),
                            ("STYLE: TODO/FIXME without owner tag — use TODO(name) format", todos)):
            if hits:
                warnings.append(f"{label} ({len(hits)} file(s)): " + " ".join(hits[:5])
                                + (f" … and {len(hits)-5} more" if len(hits) > 5 else ""))
        if code_count > 200:
            warnings.append(f"NOTE: scanned the first 200 of {code_count} staged source files (hook time budget).")
        if warnings:
            print(json.dumps({"systemMessage": "Commit validation warnings:\n" + "\n".join(warnings)}, ensure_ascii=False))
        return 0
    except (TimeoutError, OSError, ValueError, TypeError, AttributeError, subprocess.TimeoutExpired) as exc:
        print(f"BLOCKED: commit validation incomplete: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
