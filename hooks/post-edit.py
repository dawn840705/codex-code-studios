"""Native edit checks: one Python process, no Bash or subprocess per file."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import re

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "scripts"))
from console_encoding import force_utf8

spec = importlib.util.spec_from_file_location("run_bash", ROOT / "run-bash.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
ANIMATOR = re.compile(r'(\b[A-Za-z0-9_]*[Aa]nim[A-Za-z0-9_]*|GetComponent<Animator>\(\))'
                      r'\.(SetBool|SetInteger|SetFloat|SetTrigger|ResetTrigger|GetBool|GetInteger|GetFloat)\("[^_"]')


def layout_settings():
    configs = []
    for name in (".codex/studio-layout.json", ".claude/studio-layout.json", ".claude/settings.json"):
        try:
            data = json.loads(Path(name).read_text(encoding="utf-8"))
            if name.endswith("settings.json"):
                data = data.get("studio", {}).get("layout", {})
            if isinstance(data, dict):
                configs.append(data)
        except (OSError, ValueError, AttributeError):
            continue

    def setting(env, key, default):
        return os.environ.get(env) or next((c[key] for c in configs if c.get(key)), default)

    unity = Path("Assets").is_dir() and Path("ProjectSettings").is_dir()
    detected = ("unity" if unity else "godot" if Path("project.godot").is_file()
                else "unreal" if any(Path.cwd().glob("*.uproject"))
                else "gamemaker" if any(Path.cwd().glob("*.yyp")) else "generic")
    engine = setting("STUDIO_ENGINE", "engine", detected)
    return setting, engine, unity


def asset_layout():
    setting, engine, unity = layout_settings()
    defaults = {"unity": (["Assets"], "pascal"), "unreal": (["Content"], "pascal"),
                "godot": (["assets", "Assets"], "snake"),
                "gamemaker": (["sprites", "sounds", "assets"], "snake")}
    roots, naming = defaults.get(engine, (["assets"], "snake"))
    roots = setting("STUDIO_ASSET_ROOTS", "assetRoots", roots)
    if isinstance(roots, str):
        roots = roots.split(":")
    if not isinstance(roots, list) or not all(isinstance(r, str) for r in roots):
        raise ValueError("assetRoots must be an array of paths or a colon-separated string")
    naming = setting("STUDIO_ASSET_NAMING", "assetNaming", naming)
    if naming not in ("pascal", "snake", "any"):
        naming = defaults.get(engine, (["assets"], "snake"))[1]
    return roots, naming, unity


def main():
    force_utf8()
    try:
        payload = runner.read_input(1)
        if not payload.strip():
            return 0
        tool = json.loads(payload).get("tool_input", {})
        paths = [tool.get("file_path", "")]
        paths += re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", tool.get("command", ""), re.M)
        paths += re.findall(r"^\*\*\* Move to: (.+)$", tool.get("command", ""), re.M)
        paths = list(dict.fromkeys(p.replace("\\", "/") for p in paths if p))
        if not paths:
            return 0
        roots, naming, unity = asset_layout()
    except (TimeoutError, ValueError, AttributeError, TypeError) as exc:
        print(f"Code Studios: {exc}; validation did not run.", file=sys.stderr)
        return 1
    messages = []
    errors = []
    for name in paths:
        file = Path(name)
        asset = any(re.search(r"(?:^|/)" + re.escape(r.rstrip("/")) + "/", name) for r in roots if r)
        if asset and file.suffix != ".meta":
            reason = ""
            if naming == "snake" and re.search(r"[A-Z\s-]", file.name):
                reason = "must be lowercase with underscores"
            elif naming == "pascal":
                if re.search(r"\s", file.name):
                    reason = "contains whitespace — use PascalCase without spaces"
                elif "-" in file.name:
                    reason = "contains a hyphen — use PascalCase or underscores"
            if reason:
                messages.append(f"NAMING [{naming}]: {name} {reason} (got: {file.name})")
            if file.suffix == ".json" and file.is_file():
                try:
                    json.loads(file.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    errors.append(f"FORMAT: {name} is not valid JSON or could not be read: {exc}")
        if re.search(r"(?:^|/)skills/[^/]+/SKILL\.md$", name):
            messages.append(f"Code Studios skill modified: {file.parent.name}. Run $skill-test static and the Codex skill validator.")
        if unity and file.is_file():
            if file.suffix in (".cs", ".shader", ".asset", ".prefab", ".mat", ".controller") \
                    and not Path(name + ".meta").is_file():
                messages.append(f"Missing Unity sidecar: {name}.meta — focus Unity Editor to generate it, then include it in the commit.")
            if file.suffix == ".cs":
                try:
                    findings = [f"{n}: {line}" for n, line in enumerate(file.read_text(encoding="utf-8-sig").splitlines(), 1)
                                if ANIMATOR.search(line)]
                except (OSError, UnicodeError) as exc:
                    print(f"Code Studios: could not check {name}: {exc}", file=sys.stderr)
                    return 1
                if findings:
                    messages.append(f"Unity Animator string access in {name}:\n" + "\n".join(findings)
                                    + "\nCache parameters with Animator.StringToHash and pass the integer hash.")
    if errors:
        print("Asset validation failed:\n" + "\n".join(errors), file=sys.stderr)
        return 2
    if messages:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
              "additionalContext": "\n".join(messages)}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
