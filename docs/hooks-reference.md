# Active Hooks

Hooks are configured in `hooks/hooks.json`, which Codex auto-discovers from the
plugin root after the user completes the hook trust review:

| Hook | Event | Trigger | Action |
| ---- | ----- | ------- | ------ |
| `validate-commit.sh` | PreToolUse (`exec_command`/`Bash`) | Commands that **begin with** `git commit` (a prefixed form — `git add -A && git commit`, `ENV=x git commit`, `git -C dir commit` — is not inspected) | Validates design doc sections and JSON data files (invalid JSON blocks); warns on hardcoded gameplay values only when `production/track.txt` is `game` |
| `validate-push.sh` | PreToolUse (`exec_command`/`Bash`) | Commands that **begin with** `git push` (same prefix rule as above) | Warns on pushes to protected branches (develop/main/master); never blocks |
| `validate-assets.sh` | PostToolUse (`apply_patch`/edit aliases) | Asset file changes | Extracts every changed path, then checks naming conventions and JSON validity |
| `unity-meta-check.sh` | PostToolUse (`apply_patch`/edit aliases) | Unity asset writes | Warns when a Unity asset has no paired `.meta` |
| `unity-animator-string-lint.sh` | PostToolUse (`apply_patch`/edit aliases) | `.cs` writes | Warns on `Animator.SetBool("literal")` instead of a cached `StringToHash` (first 5 findings per file) |
| `session-start.sh` | SessionStart | Session begins | Loads sprint context, milestone, git activity; detects and previews active session state file for recovery; prints the always-active rule summaries (self-loop, route hint, autonomy contract) |
| `detect-gaps.sh` | SessionStart | Session begins | Detects fresh projects (suggests $start — only when `detect-project-type.sh` also says `unknown`) and missing documentation when code/prototypes exist, suggests $reverse-document or $project-stage-detect |
| `detect-project-type.sh` | SessionStart | Session begins | Prints `PROJECT_TYPE=<game\|web\|mobile\|service\|unknown>` so the orchestrator activates the right agent pack |
| `pre-compact.sh` | PreCompact | Context compression | Dumps session state (active.md, modified files, WIP markers across the detected design roots; each list capped at 30 lines) into conversation before compaction so it survives summarization |
| `post-compact.sh` | PostCompact | After compaction | Returns JSON context instructing Codex to restore `active.md` |
| `session-stop.sh` | SessionEnd | Actual session shutdown | Summarizes accomplishments and updates session log |
| `log-agent.sh` | SubagentStart | Agent spawned | Audit trail start — logs subagent invocation with timestamp |
| `log-agent-stop.sh` | SubagentStop | Agent stops | Audit trail stop — completes subagent record |
| `validate-skill-change.sh` | PostToolUse (`apply_patch`/edit aliases) | `skills/*/SKILL.md` changes | Returns JSON context advising `$skill-test` and Codex skill validation — once per skill per session (keyed by the payload's `session_id`) |

The legacy `notify.sh` remains in the repository for Claude compatibility but is
not registered because Codex has no `Notification` hook event.

## Which hooks can actually block

A hook that only ever exits 0 has never rendered a verdict, and "no verdict" is
not "pass" — the same rule [`deterministic-gates.md`](./deterministic-gates.md)
states for gates. Read this table before treating a silent hook as a green light.

| Hook | Highest exit code | Can it block? |
| ---- | ----------------- | ------------- |
| `validate-commit.sh` | 2 | **Yes** — blocks the `git commit` |
| `validate-push.sh` | 0 | No — protected-branch reminder only |
| `validate-assets.sh` | 2 | **Yes** — invalid JSON only; naming stays advisory |
| `validate-skill-change.sh` | 0 | No — advisory only |
| `unity-meta-check.sh` | 0 | No — advisory only |
| `unity-animator-string-lint.sh` | 0 | No — advisory only |
| `detect-gaps.sh` | 0 | No — advisory only |
| `session-start.sh` · `session-stop.sh` · `pre-compact.sh` | 0 | No — context injection, not judgment |
| `post-compact.sh` | 0 | No — context injection, not judgment |
| `log-agent.sh` · `log-agent-stop.sh` · `detect-project-type.sh` | 0 | No — audit trail / detection output |

Only `validate-commit.sh` and `validate-assets.sh` can render a blocking verdict.
Everything else informs.

---

## Layout detection — `hooks/lib/detect-layout.sh`

**Any hook that touches a project path must get that path from the helper, never
from a hardcoded literal.** Detection lives in exactly one file so the hooks
cannot drift apart again.

They did drift: `detect-gaps.sh`, `validate-commit.sh` and `validate-assets.sh`
each assumed `src/`, `assets/` and `design/gdd/`. Unity forces `Assets/` +
`ProjectSettings/` and keeps code under `Assets/**/*.cs`, so on a Unity project
the first hook reported a 60-script codebase as `NEW PROJECT` (and exited before
its own gap checks ran), the second matched nothing on every commit, and the
third skipped every file — hiding the fact that its lowercase-only naming rule
would reject `PlayerController.cs`, which is the *correct* Unity name.

### What it exports

| Variable | Unity | Godot | Unreal | Generic |
| --- | --- | --- | --- | --- |
| `STUDIO_ENGINE` | `unity` | `godot` | `unreal` | `generic` |
| `STUDIO_SRC_ROOTS` | `Assets` | `.` | `Source`, `Plugins` | `src`, `lib`, `app`, `packages` |
| `STUDIO_SRC_EXTS` | `cs` | `gd cs` | `cpp h hpp` | `gd cs cpp c h hpp rs py js ts …` |
| `STUDIO_DESIGN_ROOTS` | every existing candidate: `design/gdd`, `Documents`, `Docs`, `docs/design`, … | | | `design/gdd`, `product/prd`, `docs/design` |
| `STUDIO_ASSET_ROOTS` | `Assets` | `assets`, `Assets` | `Content` | `assets` |
| `STUDIO_ASSET_NAMING` | `pascal` | `snake` | `pascal` | `snake` |

Helper functions: `studio_find_sources`, `studio_count_sources`,
`studio_count_design_docs`, `studio_design_doc_exists`, `studio_find_subdir`,
`studio_is_engine_project`, `studio_path_has_ext`, `studio_asset_root_regex`,
`studio_naming_violation`, `studio_find_design_docs`. Generated directories (`Library/`, `Temp/`,
`node_modules/`, `Intermediate/`, …) are pruned from every walk — Unity's
`Library/` alone would blow the SessionStart timeout.

Design roots are **not exclusive**: every candidate that exists is kept, because
a Unity project commonly carries both its own `Documents/` tree and a
`design/gdd/` tree copied from the template.

### Naming conventions are per-engine

`pascal` is not a relaxation of `snake` — it is a different correct answer.
Unity requires a `.cs` file name to match its class name, so `PlayerController.cs`,
`CARD_MaxHP.asset` and `Monster_Base.prefab` are all correct and none of them
can be lowercased. Under `pascal` only whitespace and hyphens are flagged. Under
`snake` (web, Godot) the original lowercase-with-underscores rule is unchanged.

### Overriding detection

Highest priority first:

1. **Environment** — `STUDIO_ENGINE`, `STUDIO_SRC_ROOTS`, `STUDIO_SRC_EXTS`,
   `STUDIO_DESIGN_ROOTS`, `STUDIO_ASSET_ROOTS`, `STUDIO_ASSET_NAMING`,
   `STUDIO_PRODUCTION_ROOTS` (colon-separated for list values).
2. **`.codex/studio-layout.json`** — the preferred project file.
3. **`.claude/studio-layout.json`** — legacy transition fallback.
4. **`.claude/settings.json`** → `"studio": { "layout": { … } }` legacy fallback.

```json
{
  "engine": "unity",
  "srcRoots": ["Assets/02.Scripts"],
  "designRoots": ["Documents/Specs", "design/gdd"],
  "productionRoots": "Documents/Plan:production/sprints",
  "assetNaming": "pascal"
}
```

Keys: `engine`, `srcRoots`, `srcExtensions`, `designRoots`, `assetRoots`,
`assetNaming`, `productionRoots`. List values accept a JSON array or a
colon-separated string; without `jq` installed only the string form is readable,
and an unreadable value falls through to detection rather than to an empty
layout.

> **`jq` caveat, concretely.** Git Bash on Windows usually has no `jq`. If you
> write `"productionRoots": ["Documents"]` there, the array is unreadable and
> the default `production/sprints` is silently kept — the warning you were
> trying to silence keeps firing. Use the string form to be portable:
> `"productionRoots": "Documents:Documents/Queue"`.

`productionRoots` is what `detect-gaps.sh` Check 5 looks in before reporting
"large codebase but no production planning". It defaults to `production/sprints`
and `production/milestones`. A project that keeps its plans somewhere else — a
`Documents/Plan.md`, a work queue, an ordering board — sets this instead of
living with a false alarm every session. It changes *where the check looks*, not
whether it runs: point it at a directory that does not exist and the warning
still fires, naming that directory.

`assetNaming` accepts `pascal`, `snake` or `any` — `any` disables the naming
check entirely for projects that carry a third-party asset store tree.

### Rules for adding a hook

1. **Source the helper, guarded.** A missing helper must never fail a hook:

   ```bash
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   if [ -f "$SCRIPT_DIR/lib/detect-layout.sh" ]; then
       . "$SCRIPT_DIR/lib/detect-layout.sh"
   else
       :  # fall back to the legacy literal paths, or exit 0
   fi
   ```

2. **Select code files by extension, not by directory.** `studio_path_has_ext`
   is portable across every engine; `^src/gameplay/` is portable across none.
3. **Stay advisory by default; block with `exit 2`.** Return advisory text as
   valid JSON (`systemMessage` or PostToolUse `additionalContext`). Reserve blocking for unambiguous, mechanical
   failures (invalid JSON), never for style opinions — and when you do block,
   **use `exit 2`, not `exit 1`.** Codex treats exit 2 plus stderr as the blocking
   result; exit 0 advisory stderr is not model context. See the
   4-code contract in [`deterministic-gates.md`](./deterministic-gates.md).
4. **`grep -E` only.** Windows Git Bash ships a grep without `-P`. Enforced by
   `tests/test_hooks_layout.py::test_no_hook_uses_perl_grep`.
5. **Cover both directions in `tests/test_hooks_layout.py`** — the engine
   project must be handled *and* the generic project must be unchanged.
