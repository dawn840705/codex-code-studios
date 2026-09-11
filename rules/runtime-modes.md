# Runtime Modes — Codex Alone, Claude Alone, or Split

**Global rule. Applies to every project and every domain.**

This studio ships twice, from two source repositories:

| Package | Runtime | Invocation | Roles live in |
|---|---|---|---|
| `codex-code-studios` | Codex | `$skill-name` | `skills/studio-orchestrator/references/roles/*.md` (45 loaded references) |
| `claude-code-studios` | Claude Code | `/skill-name` | `agents/*.md` (45 installed agents) |

Same studio, two runtimes. A project can be worked by either one alone, or by
both at once. **Which of those is happening changes what this plugin should
do**, and it is not inferable from the code in front of you.

## The three modes

| Mode | Who works the project | This plugin's job |
|---|---|---|
| `codex` | Codex only, every line | **Full studio.** `$studio-orchestrator` loads the role references it needs, runs every gate, owns every artifact. This is the default. |
| `claude` | Claude Code only, every line | **Stand down.** `claude-code-studios` owns the work. Do not load role references, do not write studio artifacts, do not run phase gates. Answer questions and do explicitly requested one-off edits. |
| `split` | Both, divided by strength | **Partial studio, partitioned.** Work only the lines this runtime owns (§ Split mode), and never write a file the other runtime owns. |

## How a session knows which mode it is in

Read **`production/runtime.txt`** in the user's project — one line, exactly one
of `codex`, `claude`, `split`. Absent means `codex`.

**Do not infer the mode from ambient signals.** A `CLAUDE.md` or a `.claude/`
directory in the project proves only that Claude Code was configured there at
some point — not that it is working this task, and not which lines it owns.
This is the same failure `production/track.txt` exists to prevent: *every
detection signal is a build artifact of a stack already chosen*, so the signal
is missing exactly when the question first matters. Ask the user and write the
answer down.

`runtime.txt` and `track.txt` are independent axes. `track.txt` says *what is
being built* (game / product); `runtime.txt` says *who is building it*. Neither
one implies the other.

## Split mode — partition write ownership before starting

[`subagent-collaboration.md`](subagent-collaboration.md) already states the rule
for parallel subagents: write ownership is partitioned before dispatch, because
two workers on one file means a lost edit, and **a lost edit is the one failure
mode that reports success.**

**Split mode is that same failure, one level up, and worse.** Two subagents at
least share an orchestrator that knows what it dispatched. Codex and Claude Code
share nothing — not a session, not a context window, not a tool log. Neither one
can see that the other just rewrote the file it is holding in memory, and the
loser of the race reports success either way.

So in `split` mode, before any work begins:

1. **Write the partition down** in `production/runtime.txt` under the mode line —
   which paths each runtime owns. Paths, not topics; a topic is not something a
   file-write can be checked against.
2. **Touch nothing outside your partition.** Not "ask first" — do not write it.
   If work requires a file the other runtime owns, report that and stop.
3. **Re-read before you edit**, every time. The file may have moved since this
   session started, and no hook will tell you.

Unpartitioned paths are unowned, and unowned means nobody writes them until the
user assigns them.

### Which strengths go to which runtime — UNDECIDED

The partition above is a mechanism, not a policy. **Who is better at what has
not been settled for this studio**, and this rule deliberately does not invent
it. Until the user fixes the split, ask for the partition per project rather
than assuming one.

When it is settled, it belongs in this section as paths, with the reasoning
attached — not as a general claim about which tool is smarter.

## Cross-repo relationship

Per [`AGENTS.md`](../AGENTS.md), **this repository is where settled common policy
lives** (user instruction, 2026-09-07). Two consequences:

- A shared studio policy landing in `claude-code-studios` first is not finished
  until it is reflected here. Sibling-first changes arrive as a port, and the
  port is the completing step — not an optional mirror.
- Do not fork a second canonical copy of a shared policy. The rule files in
  `rules/` are per-package resources and are expected to exist in both trees;
  the *policy* they encode has one home, and it is this one.

As `AGENTS.md` records, the root `CLAUDE.md` and `.claude-plugin/` here are a
transition-compatibility layer, not a source of truth for Codex behavior.
