# Active Hooks

Hooks are configured in `hooks/hooks.json`, which Codex auto-discovers from the
plugin root after the user completes the hook trust review:

`PostToolUse` registers only `post-edit.py`: it reads input once and checks changed
paths directly in Python without starting Bash or child processes. It preserves
layout overrides, naming, JSON, skill, Unity meta and Animator checks and emits
one combined JSON response. `run-bash.py` closes private stdin and terminates
its own process tree on timeout, with three seconds reserved for cleanup.
On Windows a kill-on-close Job Object also owns reparented Git Bash descendants.
`PreToolUse` commit validation uses `pre-commit.py`: one bounded Git query and
native file scanning, preserving section/JSON/source advice without spawning a
shell command for every file or section. `validate-commit.sh` is a compatibility
entry point that delegates to that same implementation.
Session-end and subagent audit scripts below are manual/optional, not registered
by default. Unity PascalCase naming remains supported by layout detection.

For local resource reduction, disable individual advisory handlers with
`enabled = false` in their existing `[hooks.state."<hook-id>"]` config table.
Keep trust hashes intact: changed definitions need normal review once; never
rewrite a hash to manufacture approval. The hook-list icon itself belongs to
the Codex UI and is not controlled by this plugin.

| Hook | Event | Trigger | Action |
| ---- | ----- | ------- | ------ |
| `pre-commit.py` | PreToolUse (`exec_command`/`Bash`) | `git commit` commands | Validates design doc sections, JSON data files, hardcoded values, TODO format with one Git query |
| `validate-push.sh` | PreToolUse (`exec_command`/`Bash`) | `git push` commands | Warns on pushes to protected branches (develop/main) |
| `post-edit.py` | PostToolUse (`apply_patch`/edit aliases) | Changed files | Native naming/JSON, skill-validation reminders, Unity `.meta` and Animator checks; no child processes |
| `session-start.sh` | SessionStart | Session begins | Loads sprint context, milestone, git activity; detects and previews active session state file for recovery |
| `detect-gaps.sh` | SessionStart | Session begins | Detects fresh projects (suggests $start) and missing documentation when code/prototypes exist, suggests $reverse-document or $project-stage-detect |
| `detect-project-type.sh` | SessionStart | Session begins | Prints `PROJECT_TYPE=<game\|web\|mobile\|service\|unknown>` so the orchestrator activates the right agent pack |
| `pre-compact.sh` | PreCompact | Context compression | Dumps session state (active.md, modified files, WIP design docs) into conversation before compaction so it survives summarization |
| `post-compact.sh` | PostCompact | After compaction | Returns JSON context instructing Codex to restore `active.md` |
| `session-stop.sh` (optional) | Manual | Explicit session summary | Summarizes accomplishments and updates session log |
| `log-agent.sh` (optional) | Manual | Explicit agent audit | Audit trail start — logs subagent invocation with timestamp |
| `log-agent-stop.sh` (optional) | Manual | Explicit agent audit | Audit trail stop — completes subagent record |

The former edit check shell scripts remain available for manual checks and
compatibility tests; they are no longer registered separately.

The legacy `notify.sh` remains in the repository for Claude compatibility but is
not registered because Codex has no `Notification` hook event.

## Which hooks can actually block

A hook that only ever exits 0 has never rendered a verdict, and "no verdict" is
not "pass" — the same rule [`deterministic-gates.md`](./deterministic-gates.md)
states for gates. Read this table before treating a silent hook as a green light.

| Hook | Highest exit code | Can it block? |
| ---- | ----------------- | ------------- |
| `validate-commit.sh` | 2 | **Yes** — blocks the `git commit` |
| `pre-commit.py` | 2 | **Yes** — invalid JSON or incomplete validation blocks the commit |
| `validate-push.sh` | 0 | No — protected-branch reminder only |
| `validate-assets.sh` | 2 | **Yes** — invalid JSON only; naming stays advisory |
| `post-edit.py` | 2 (invalid JSON), 1 (incomplete check) | PostToolUse feedback; cannot undo the completed edit |
| `validate-skill-change.sh` | 0 | No — advisory only |
| `unity-meta-check.sh` | 0 | No — advisory only |
| `unity-animator-string-lint.sh` | 0 | No — advisory only |
| `detect-gaps.sh` | 0 | No — advisory only |
| `session-start.sh` · `session-stop.sh` · `pre-compact.sh` | 0 | No — context injection, not judgment |
| `post-compact.sh` | 0 | No — context injection, not judgment |
| `log-agent.sh` · `log-agent-stop.sh` · `detect-project-type.sh` | 0 | No — audit trail / detection output |

`pre-commit.py` (and its compatibility wrapper) can prevent a commit. The manual asset validator and
`post-edit.py` also return a nonzero verdict on invalid JSON, but PostToolUse
runs after the write. Treat its failure as a repair request, not a prevented write.

---

## Layout detection — `hooks/lib/detect-layout.sh`

Native hooks share `layout_settings()` / `asset_layout()` in `post-edit.py`.
Bash hooks share `lib/detect-layout.sh`. Keep their engine defaults and
env → Codex config → legacy config precedence aligned; do not put separate
layout assumptions in individual checks.

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
`studio_naming_violation`. Generated directories (`Library/`, `Temp/`,
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

## 2026-10-08 — Windows resource fix and local application

The 2026-10-05 inbox report identified orphaned Bash processes after wrapper
termination. The installed 0.7.5 fix was recovered into source, then strengthened
with Windows Job Object ownership. Native edit checks replace the four hot-path
wrappers; missing layout config files no longer spawn nested shells just to
report absence. Shell files are checked out with LF through `.gitattributes`.

The workstation now installs 0.7.6 through the local `code-studios` marketplace
using the regular Codex installer. Installed runtime hashes match source. Local
hook states disable push reminders, startup gap/type suggestions, session-end
logging and subagent start/stop logging (six states); commit validation, prompt
advice and compaction recovery remain enabled. Previous config was backed up,
and existing trust hashes were preserved. Changed definitions require normal
hook review; this plugin cannot hide the app's hook-list icon.

Validated: 91 skill validators, 136-file skill/role lint (existing baseline only),
17 shell syntax checks, plugin manifest tests and normal CLI installation,
Windows timeout/input regression checks, native edit feedback/invalid-JSON checks,
layout override handling, and 20 repeated native edits in 3.51 seconds. The
native edit hook is tested to start no child processes. Commit scans now use one
bounded Git query and a native file loop, replacing the legacy per-document
section subprocesses that also timed out on large Unity commits.

Full offline suite, executed in partitions: **670 passed, 6 skipped, 40 subtests
passed** (676 collected). Initial bounded Bash commit scans timed out on four
Unity regressions; all ten commit regressions passed after the native migration
(9.06 seconds). Production hook deadlines were not increased. Compatibility
layout checks use a separate manual-test budget.
