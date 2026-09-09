---
name: api-cost-gate
description: "Pre-flight cost approval gate for any paid AI API call (image / 3D / audio / video / text generation services). Forces explicit 4-point disclosure (call type / cost estimate / purpose / use) before invocation. Use before any Suno/ElevenLabs/Midjourney/OpenAI/Tripo/etc. paid call. Use when user says 'check cost first', 'cost gate', 'approve API call'."
---

## Purpose

Solo developers and small teams using paid AI APIs (Suno, ElevenLabs, Midjourney, OpenAI, Tripo, etc.) face two failure modes:

1. **Surprise bills** — automated retries, runaway loops, accidentally-expensive calls (e.g. 10-minute music generation when 30 seconds was intended).
2. **Wasted spend** — calls made before the *use* is clear, producing assets that get discarded.

This skill enforces a **pre-flight 4-point disclosure** before any paid call. The agent cannot invoke the API until the user has reviewed and approved:

1. **Call type** — exact endpoint / mode / model.
2. **Cost estimate** — credits / characters / dollars (with current balance if known).
3. **Purpose** — what we're producing and why.
4. **Use plan** — where the output will live, how it will be evaluated, what triggers acceptance.

Auto-mode does **not** override this gate. Even when the agent is running autonomously, paid API calls require explicit user OK each time.

Writes: `Documents/api-cost-log.md` (one appended row per approved call); nothing else is created or modified.

---

## Phase 1: Identify the call

From `the invocation arguments`:
- `$1` = service name (e.g. `suno`, `elevenlabs`, `midjourney`, `openai`)
- `$2` = brief description (e.g. `combat-bgm-30s`, `npc-dialogue-line`, `concept-art-key-visual`)

If args missing, ask the user what call they intend to make.

---

## Phase 2: Compose the 4-point disclosure

Produce a short, unambiguous block:

```
=== Paid API Call — Approval Required ===

1. Call type:
   <service> <endpoint> — <model> <mode>
   Example: Suno /api/v1/generate — V5, custom mode, instrumental

2. Cost estimate:
   ~<N> <unit>  (current balance: <M>)
   Example: ~12 credits  (current balance: 486)

3. Purpose:
   <what + why, 1-2 sentences>
   Example: Voice-of-Peace BGM bed for chapter 1 radio segment.
            First sample to lock chapter 1 musical tone.

4. Use plan:
   <where it lives + how it's evaluated + acceptance criteria>
   Example: Lands in Tools/SunoAPI/output/ as workshop. If A/B-compared
            against existing anchor (or pilot-anchored if first), promote
            to Documents/AudioDesign/Anchors/ with prompt.txt.

→ Approve? (Y / N / modify)
```

The 4-point block is **engine-agnostic / service-agnostic**. The pattern works for any paid API.

---

## Phase 3: Wait for explicit user approval

Do **not** make the API call until the user responds with explicit approval. Acceptable approvals:

- `Y` / `OK` / `진행` / `approved` / `go` — proceed.
- `N` / `cancel` / `stop` — abort.
- `modify <change>` — adjust the call per change, re-show the 4-point block, wait again.

Treat ambiguous responses (silence, unrelated message, `maybe`) as **not approved** — do not call.

If `the invocation arguments` was originated *by the user themselves* with full intent (e.g. they typed `$api-cost-gate suno combat-bgm-30s` and immediately follow with `Y` in the same message), the gate is satisfied — but only if all 4 points are still presented and acknowledged.

---

## Phase 4: Log the approval (optional but recommended)

After approval, append to a project-level cost log:

```
Documents/api-cost-log.md
```

```
| Date       | Service     | Call                  | Cost   | Result                                  |
|------------|-------------|-----------------------|--------|-----------------------------------------|
| 2026-05-03 | Suno        | combat-bgm-30s V5     | 12 cr  | Tools/SunoAPI/output/<id>/ — pending    |
```

This makes monthly billing reconcilable and surfaces calls that produced *no kept output* — a useful signal for prompt iteration efficiency.

---

## Phase 5: Hand off to the actual call

Once approved, invoke the API call via whatever mechanism the project uses (CLI script, MCP tool, HTTP). Treat the call's output handling as a separate concern — this skill is only the gate, not the entire workflow.

---

## When NOT to use this skill

- **Free / local calls** — local LLM, sandboxed model, no-cost endpoint. Gate adds friction with no benefit.
- **Pre-approved batch operations** — if the user explicitly approved "generate 10 variations" as a single batch, individual variation calls don't need re-gating; document the batch approval scope and proceed.
- **Read-only / metadata calls** — fetching credit balance, listing voices, getting account info. These are typically free even on paid services.
- **The cost is genuinely trivial and bounded** (e.g. <$0.01 with hard ceiling) **and** the user has standing approval. Document the standing approval explicitly.

---

## Generalises across services

Confirmed services where this gate has prevented surprise spend or wasted output:

| Service | Unit | Notes |
|---|---|---|
| Suno (music) | credits | 1 call ≈ 10-20 credits, 2 variants per call |
| ElevenLabs (TTS / SFX / music) | characters | TTS ≈ 1 char / char, SFX ≈ 100 char/sec, Music ≈ 1000 char/sec |
| Midjourney / Stable Diffusion (image) | seconds / generations | varies by tier |
| Tripo (3D) | credits | varies by mesh complexity |
| OpenAI / Anthropic (text) | tokens | input + output, varies by model |
| remove.bg (background removal) | credits | `size=preview` ≈ 0.25 cr, `size=full` ≈ 1 cr per image — a 4× spread, so preview is the default. Gate is wired into `$remove-bg`; `scripts/removebg.py estimate` produces point 2 without charging. |

Add your service to the table when adopted. The 4-point disclosure works identically for all of them.

**Where a service has a dedicated skill, use it.** `$remove-bg` already embeds
this gate (Phases 2-3) and backs the estimate with a real balance lookup, so
invoking `$api-cost-gate` separately just duplicates the block. This skill is
for services that have no wrapper yet.
