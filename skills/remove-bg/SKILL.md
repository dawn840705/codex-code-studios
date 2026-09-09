---
name: remove-bg
description: "Remove image backgrounds via the remove.bg API — single image, folder batch, or straight from the asset manifest. Enforces the $api-cost-gate 4-point disclosure before any paid call, runs scripts/removebg.py (exit code is the verdict), and writes results back to design/assets/asset-manifest.md. Use when the user says 'remove background', '배경 제거', '누끼', 'cut out', 'transparent PNG', or wants sprite/product/character art alpha-cut for production."
---

# Remove Background (remove.bg)

Background removal is a **paid API call**, so this skill is built around one
rule: nothing gets charged before the user has seen what it costs and said yes.

The split of labor is deliberate:

- **`scripts/removebg.py` decides.** Input discovery, pre-flight rejection, cost
  estimation, HTTP, retries, and the pass/fail verdict all live in the script.
  Its **exit code is the verdict** — do not re-derive success by reading stdout.
- **This skill narrates.** It composes the cost disclosure, gets approval, and
  translates the script's JSON report into the project's asset manifest.

**Exit code contract** (`../../docs/deterministic-gates.md`):

| Code | Meaning | What you report |
|---|---|---|
| `0` | every requested image processed | **PASS** |
| `1` | partial failure, or everything skipped | **CONCERNS** — list the failures |
| `2` | all failed / 402 credits / 403 auth / `--max-calls` tripped | **FAIL** — stop, do not retry blind |
| `3` | could not run (no API key, bad path) | **BLOCKED** — no verdict was produced; never read this as a pass |

---

## Phase 0: Parse arguments and check the key

Parse `the invocation arguments`:

- **Target** — a file path, a folder, an `http(s)` URL, or `manifest:<context>`
  (pull the asset list from `design/assets/asset-manifest.md`).
- `--size` — `preview` (≈0.25 credits, ≤0.25MP) or `full` (≈1 credit, up to 50MP).
  **Default to `preview`.** Preview is the right default for design review; full
  size is for final production art only.
- `--type` — `auto` / `person` / `product` / `car` / `animal` / `graphics`.
  For game sprites and UI icons, `product` or `graphics` usually beats `auto`.
- `--out` — output directory. Default `design/assets/cutout/` for manifest runs,
  else a `cutout/` sibling of the input.
- `--execute` — the user has pre-approved; still show the disclosure, but accept
  it as answered in Phase 3.

If no argument is given, check whether `design/assets/asset-manifest.md` exists:

- If it exists, take the assets whose category is a 2D/sprite/UI type as the
  target. The Phase 2 disclosure shows that scope before anything is charged;
  the user narrows it there with `modify`.
- If it does not exist, fail with:
  > "Usage: `$remove-bg <file|folder|url>` — e.g. `$remove-bg design/assets/raw/hero.png`
  > Or `$remove-bg manifest:tower-defense` once you have an asset manifest."

**Key check — run this first, before anything else:**

```
Bash: python3 scripts/removebg.py account
```

Exit `3` means no key is configured. Stop and tell the user:

> **BLOCKED** — no remove.bg API key. Get one at
> https://www.remove.bg/dashboard#api-key then `export REMOVE_BG_API_KEY=<key>`
> (or pass `--api-key-file <path>`). Nothing was called, nothing was charged.

Never ask the user to paste the key into the chat and never write a key into a
file in the repo. If they want it persisted, point them at their shell profile
or a gitignored path used with `--api-key-file`.

---

## Phase 1: Build the plan (no charge)

Run the estimator. This makes **zero** billable calls:

```
Bash: python3 scripts/removebg.py estimate <target> \
        --out <out-dir> --size <size> --type <type> \
        --check-balance --json
```

Read the JSON. The fields that matter:

- `inputs_found` / `billable_calls` / `skipped` — what will and won't be called.
- `estimated_credits_total` — the estimate. It is an *estimate*; say so.
- `account.total_credits` and `account.free_calls_remaining` — the real balance.
- `items[]` — per-image action, with a `reason` on every skip (already exists,
  empty file, over the 22MB upload limit).

If `billable_calls` is `0`, there is nothing to charge for. Report why (usually
"outputs already exist") and offer `--overwrite`. Do not proceed to Phase 3.

If the estimate exceeds the balance, stop with **FAIL** before calling anything:

> **FAIL** — plan needs ~[N] credits, balance is [M]. Reduce scope, switch to
> `--size preview`, or top up first.

---

## Phase 2: Compose the cost disclosure

This is `$api-cost-gate`'s 4-point block, filled from the Phase 1 JSON. Do not
paraphrase it into a casual sentence — the format is the point.

```
=== Paid API Call — Approval Required ===

1. Call type:
   remove.bg POST /v1.0/removebg — size=<size>, type=<type>, format=<format>
   <N> images, batched

2. Cost estimate:
   ~<estimated_credits_total> credits  (current balance: <total_credits>,
   free preview calls left: <free_calls_remaining>)
   Estimate only — the charged amount comes back in X-Credits-Charged.

3. Purpose:
   <what these cutouts are for, 1-2 sentences — pull it from the manifest
   context or ask>

4. Use plan:
   Outputs land in <out-dir> as <stem>-nobg.png.
   Report: <out-dir>/removebg-report.json
   Accepted when: alpha edges are clean at target display size; on rejection
   re-run that image with a tighter --type or --roi.

→ Approve? (Y / N / modify)
```

---

## Phase 3: Wait for explicit approval

Do **not** call the API until the user answers. Acceptable approvals: `Y`, `OK`,
`진행`, `approved`, `go`. Treat silence, `maybe`, or an unrelated message as
**not approved**.

- `N` / `cancel` / `중단` → stop. Nothing charged.
- `modify <change>` → adjust the flags, re-run Phase 1, re-show the block, wait again.

Auto-mode does not override this gate. If the skill was invoked with
`--execute` *by the user themselves*, the gate is satisfied — but the 4-point
block still has to be printed so the cost is on the record.

---

## Phase 4: Execute

```
Bash: python3 scripts/removebg.py run <target> \
        --out <out-dir> --size <size> --type <type> \
        --max-calls <billable_calls from Phase 1> \
        --manifest <out-dir>/removebg-report.json
```

`--max-calls` is a seatbelt: if the input set grew between estimate and run, the
script aborts (exit `2`) instead of silently charging more than what was approved.

**Read the exit code, then explain it with the report.** Never the other way round.

- `0` → **PASS**.
- `1` → **CONCERNS**. Name each failed image and its `reason` from the report.
  Common causes: `unknown_foreground` (no clear subject — try an explicit
  `--type` or an `--roi`), `file_too_large`, unsupported format.
- `2` → **FAIL**. If the reason is `402 insufficient credits` or
  `403 authentication failed`, stop and hand it to the user; do not retry.
- `3` → **BLOCKED**. The gate did not run. Fix the invocation and start over.

The report's `credits_charged_total` is the **measured** spend. If it differs
meaningfully from the estimate, say so plainly — the estimate table in the script
is a documented approximation, and a drift is worth flagging.

---

## Phase 5: Update the asset manifest

Only when `design/assets/asset-manifest.md` exists and the run touched assets
tracked in it.

For each `results[]` record with `status: "ok"`, find the matching asset row and
update it:

- Status `Needed` → `In Progress` (a cutout exists but has not been reviewed).
  Do **not** jump to `Done` — background removal is a processing step, not an
  approval.
- Append the cutout path to the row's Spec File cell or a `Cutout` column.

Also update the Progress Summary counts. Write the manifest and report the path
and the revert command (`git checkout -- design/assets/asset-manifest.md`). The
JSON report stays on disk either way.

If no manifest exists, skip this phase silently. Do not create one here; that is
`$asset-spec`'s job.

---

## Phase 6: Close — recommended next steps

Report in this shape:

```
=== $remove-bg — <PASS | CONCERNS | FAIL | BLOCKED> ===
  gate      : scripts/removebg.py run → exit <code>
  processed : <ok> ok · <failed> failed · <skipped> skipped
  charged   : <credits_charged_total> credits (estimated ~<estimate>)
  outputs   : <out-dir>
  report    : <out-dir>/removebg-report.json
```

Recommended next — take [A] unless the verdict was CONCERNS, then name [B] with
the flags you would change. [B] and [C] charge again: they re-enter Phase 1-3 and
never run without a fresh disclosure and approval.

- `[A] Review the cutouts — $asset-audit` (validate delivered assets against specs)
- `[B] Re-run the failures with a tighter --type / --roi`
- `[C] Re-run at --size full for the ones that passed review`

**Follow-up handoff:** cutouts are raw output, not approved art. Route them
through `$asset-audit` before they are treated as production-ready, and let
`art-director` judge edge quality if the project has an art bible.

---

## Cost discipline

- **`--size preview` is the default and stays the default.** Preview is ~0.25
  credits against ~1 for full — a 4× difference. Only go full for assets that
  have already passed review at preview size.
- **Never loop-retry a failed image automatically.** Each retry charges. A
  failure means the parameters were wrong; change them, then ask again.
- **`--max-calls` on every batch.** It is the difference between a bounded bill
  and an unbounded one.
- The free tier is preview-only and limited; `account` reports
  `free_calls_remaining` so you can tell the user when it runs out.

## Parameter cheatsheet

| Need | Flags |
|---|---|
| Game sprite / UI icon | `--type graphics --size preview` |
| Character / NPC art | `--type person --crop --crop-margin 5%` |
| Product or item art | `--type product --add-shadow` |
| Alpha mask only (engine compositing) | `--channels alpha` |
| Composite onto a flat color | `--bg-color 81d4fa` |
| Subject in a known region | `--roi '10% 10% 90% 90%'` |
| Hard edges, no soft alpha | `--no-semitransparency` |

Full parameter list: `python3 scripts/removebg.py run --help` ·
API reference: https://www.remove.bg/api
