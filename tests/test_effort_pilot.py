import json
import subprocess
import sys

import pytest

import effort_pilot as pilot


@pytest.mark.parametrize("message,expected", [("91", True), ("90", False), ("There are 91.", False)])
def test_independent_verifier_checks_exact_final_message(tmp_path, message, expected):
    path = tmp_path / "events"
    path.write_text('\n'.join(json.dumps(x) for x in [
        {"type": "item.completed", "item": {"type": "command_execution", "text": "91"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": message}},
        {"type": "turn.completed"}]), encoding="utf-8")
    assert pilot.verify(path, "91") is expected


def test_verifier_rejects_progress_and_failure(tmp_path):
    path = tmp_path / "events"
    path.write_text('{"type":"item.completed","item":{"type":"command_execution","text":"91"}}\n'
                    '{"type":"turn.completed"}', encoding="utf-8")
    assert not pilot.verify(path, "91")
    path.write_text('{"type":"turn.failed"}', encoding="utf-8")
    assert not pilot.verify(path, "91")


def test_pilot_snapshot_and_dispatch_cap(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "skills/a").mkdir(parents=True)
    (repo / "skills/a/SKILL.md").write_text("one", encoding="utf-8")
    (repo / '.codex-plugin').mkdir()
    (repo / '.codex-plugin/plugin.json').write_text('{"version":"0.7.0"}')
    (repo / 'hooks').mkdir()
    (repo / 'hooks/hooks.json').write_text('{"hooks":{"SessionStart":[]}}')
    for argv in (["git", "init", "--quiet"], ["git", "add", "."],
                 ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                  "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture"]):
        subprocess.run(argv, cwd=repo, check=True, capture_output=True)
    # The uncommitted edit must never leak into just one arm.
    (repo / "skills/a/SKILL.md").write_text("uncommitted", encoding="utf-8")
    output = tmp_path / "pilot"
    plan = pilot.prepare(repo, output, "fixed", ["low", "medium", "high"], "TEST fake only")
    assert (output / "snapshot/skills/a/SKILL.md").read_text() == "one"
    assert plan["expected"] == "1" and sorted(plan["order"]) == ["auto", "high", "medium"]
    cli = tmp_path / "fake-codex"
    cli.write_text("#!" + sys.executable + '\nimport json,sys\nsys.stdin.read()\n'
                   'print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":"1"}}))\n'
                   'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":4,"cached_input_tokens":0,"output_tokens":1}}))\n')
    cli.chmod(0o700)
    result = pilot.run(output, executable=str(cli), standalone=True)
    assert result["status"] == "completed" and len(result["runs"]) == 3
    assert all(r["success"] and r["model"] == "fixed" for r in result["runs"])
    assert all(r["total_usage"] is None and r["applied_effort"] is None for r in result["runs"])
    with pytest.raises(FileExistsError):
        pilot.run(output, executable=str(cli), standalone=True)
    (output / "snapshot/new-file").write_text("changed")
    with pytest.raises(ValueError, match="snapshot changed"):
        pilot.run(output, executable=str(cli), standalone=True)
    # Exercise all 27 dispatches with a local deterministic fake, never a model.
    expanded = tmp_path / 'expanded'
    pilot.prepare(repo, expanded, 'fixed', ['low', 'medium', 'high'], 'TEST fake only',
                  cases=pilot.CASES, repetitions=3)
    cli.write_text('#!' + sys.executable + '\nimport json,sys\nprompt=sys.stdin.read()\n'
                   'answer="0.7.0" if "version" in prompt else ("[\\\"SessionStart\\\"]" if "hooks/hooks.json" in prompt else "1")\n'
                   'print(json.dumps({"type":"item.completed","item":{"type":"agent_message","text":answer}}))\n'
                   'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":4,"cached_input_tokens":0,"output_tokens":1}}))\n')
    result = pilot.run(expanded, executable=str(cli), remaining_percent=50, standalone=True)
    assert result['status'] == 'completed' and len(result['runs']) == 27
    assert all(r['success'] and r['source_unchanged'] for r in result['runs'])
    assert len(result['by_case_and_arm']) == 9
    assert all(g['attempted'] == 3 and g['successes'] == 3 and g['execution_input_plus_output_tokens'] == 15
               for g in result['by_case_and_arm'])


def test_balanced_repetitions_and_limit():
    jobs = pilot.schedule(pilot.CASES, 3, 42)
    assert len(jobs) == 27
    assert jobs == pilot.schedule(pilot.CASES, 3, 42)
    for case in pilot.CASES:
        subset = [j for j in jobs if j['case'] == case]
        for position in range(3):
            assert {subset[position + 3 * i]['arm'] for i in range(3)} == {'auto', 'high', 'medium'}
    for cases, repetitions in [(pilot.CASES, 4), (['count-skills'] * 2, 1), ([], 1)]:
        with pytest.raises(ValueError):
            pilot.schedule(cases, repetitions, 42)


def test_json_verifier_ignores_whitespace_not_semantics(tmp_path):
    path = tmp_path / 'events'
    path.write_text('\n'.join(json.dumps(e) for e in [
        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '[ "A", "B" ]'}},
        {'type': 'turn.completed'}]), encoding='utf-8')
    assert pilot.verify(path, '["A","B"]', 'json')
    assert not pilot.verify(path, '["B","A"]', 'json')


def test_budget_standalone_environment_gates_before_dispatch(tmp_path, monkeypatch):
    output = tmp_path / 'batch'
    output.mkdir()
    (output / 'snapshot').mkdir()
    definitions = {'count-skills': {'prompt': 'test', 'expected': '1', 'format': 'text'}}
    monkeypatch.setattr(pilot, 'case_definitions', lambda _: definitions)
    monkeypatch.setattr(pilot, 'environment', lambda: {'test': 'fixed'})
    jobs = pilot.schedule(['count-skills'], 3, 42)
    plan = {'cases': ['count-skills'], 'repetitions_per_arm': 3, 'seed': 42,
            'jobs': jobs, 'maximum_dispatches': 9, 'timeout_seconds_per_dispatch': 60,
            'definitions': definitions, 'implementation_sha256': pilot.implementation_hash(),
            'initial_tree_sha256': pilot.tree_hash(output / 'snapshot'), 'environment': {'test': 'fixed'}}
    pilot.effort.atomic_json(output / 'manifest.json', plan)
    for remaining in (None, 3, -1, 101, float('nan')):
        with pytest.raises(ValueError, match='percentage'):
            pilot.run(output, remaining_percent=remaining, standalone=True)
    with pytest.raises(ValueError, match='standalone'):
        pilot.run(output, remaining_percent=50)
    monkeypatch.setattr(pilot, 'environment', lambda: {'test': 'changed'})
    with pytest.raises(ValueError, match='environment'):
        pilot.run(output, remaining_percent=50, standalone=True)
    assert not (output / 'dispatch-claim').exists()


def test_aggregate_counts_failures_and_propagates_missing_usage():
    plan = {'cases': ['count-skills'], 'repetitions_per_arm': 3}
    rows = [{'case': 'count-skills', 'arm': 'auto', 'success': ok, 'wall_seconds': seconds,
             'execution_usage': usage} for ok, seconds, usage in
            [(True, 1, {'input_tokens': 10, 'output_tokens': 3, 'cached_input_tokens': 8}),
             (False, 9, None)]]
    result = pilot.aggregate(plan, rows)
    auto = next(r for r in result if r['arm'] == 'auto')
    assert auto['attempted'] == 2 and auto['success_rate'] == .5
    assert auto['median_seconds'] == 5 and auto['execution_input_plus_output_tokens'] is None
    assert result[0]['success_rate'] is None
    auto = pilot.aggregate(plan, rows[:1])[-1]
    assert auto['execution_input_plus_output_tokens'] == 13
    assert auto['total_usage'] is None
