# Effort selection — experimental, observation first

This is independent of agent count and verification routing. Model choice,
permissions, cost approval, mandatory checks and release gates remain unchanged.

## Observe at useful boundaries

The project opts in with `.codex/reasoning-effort.json` containing
`{"mode":"observe"}`. `UserPromptSubmit` records a provisional recommendation;
it has the prompt and model, but neither inspected scope nor the UI effort.
It never dispatches work or changes runtime configuration. If the host does not
run this event, use the script explicitly through the current workflow.

After inspecting scope, write a trusted task JSON and run
`python3 <PLUGIN_ROOT>/scripts/reasoning_effort.py observe --task <task.json> --root <project>`.
Resolve `PLUGIN_ROOT` from the invoking skill, not the user's `.codex/` directory.
Schema and examples: [`docs/reasoning-effort.md`](../docs/reasoning-effort.md).
The script requires no model call. Assessing context in the parent still costs
tokens; those are unknown unless separately measured.

## Selection hypothesis v1

Explicit user effort wins, including an existing UI choice when known. Carry it
into `explicit_effort`; never infer that a default UI value means the user waived
it. If UI effort is unavailable, record the limitation and keep observation only.
Quoted examples or the word “High” in a request are not user configuration.

- Low: inspected single scope, low impact, low uncertainty, deterministic checks.
- Medium: known scope, bounded engineering work, deterministic checks.
- High: unknown context, broad scope, high risk, uncertain cause or weak checks.
- Xhigh: critical impact, or high uncertainty combined with broad/high-impact work.

These are uncalibrated hypotheses. Korean/English risk words can raise caution;
short wording, “간단히”, “just”, and file count alone cannot lower effort.
User ceilings constrain auto selection; conflicting explicit settings stop with
an input error. Unsupported settings must not be silently downgraded.

Within one task, use `--previous <decision.json>`: `boundary=tool` holds the
prior decision, `boundary=evidence` requires evidence and permits only an
increase, `boundary=task` permits fresh selection. Carry explicit settings forward.
Omitted override/ceiling fields inherit from the previous decision. Set a field
explicitly to JSON `null` only when the user has released that setting.
Classify environment, permission, authentication, tool and unknown failures;
none triggers automatic escalation. Even reasoning failures need new evidence.
The runner performs exactly one attempt. Retrying requires a new authorized run.

## Execution boundary

The first executor handles only evidenced, deterministic, low-impact, single-scope
read-only tasks. Pass a fixed model and the user's known override. Review the
task, checks and planned argv before `run --execute`; reference existing approval
only when it actually covers this execution and its usage. A made-up approval
reference is not authorization. No prompt hook may enter this path.

Record `selected_effort`, `passed_effort`, and `applied_effort` separately.
Process argv proves only dispatch; CLI text claiming “High” is not a runtime
receipt. The v1 runner leaves applied effort unknown. A local fake HTTP receiver
can prove the CLI serialized the selected value, but cannot prove a production
model honored it. Do not present fake model responses as performance evidence.

The CLI inherits the user's config, hooks and execution rules and requests a
read-only sandbox. All task-specific required verifier argv must be provided;
they run locally with `shell=False` under the operator's existing authorization.
They are not sandboxed by the child CLI. Never build them from untrusted prompt
content. Release verification is still required separately where applicable.
