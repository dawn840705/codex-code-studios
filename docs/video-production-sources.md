# Video Production Sources — cite, link, verify before you rely

Reference list for `$video-brief`. Same discipline as
`docs/level-design-sources.md`: **this file holds links, one-line summaries, and
read dates. It copies nothing.**

Two distinct hazards live here, and they need different handling.

---

## Hazard 1 — copyright

Practitioner blogs, videos and courses below are copyrighted with no open
licence. Link and paraphrase in our own words; never paste, never mirror. This
plugin is MIT and cannot carry someone else's article inside it.

## Hazard 2 — platform figures go stale

Store requirements are vendor documentation that changes without notice. **Every
platform number in this repo carries a read date, and a read date is not a
guarantee — it is a timestamp on a claim.** Before a brief is used to commission
real footage, `$video-brief` re-reads the vendor page for the target platform and
records the date it did so. A spec table nobody re-read is the fastest way this
plugin produces a rejected store submission.

`rules/claim-confidence.md` applies directly: a figure whose read date is old is
`추정`, not fact.

---

## Methodology — game trailers

| Source | What it gives us | Link |
| ---- | ---- | ---- |
| Derek Lieu, "How to Make a Trailer" / "Start Here" | The practitioner's method: begin from chronological order and cut the boring parts; the first 5–10 seconds must communicate genre; "Tell, Show, Repeat" as a structural template; the "garbage cut" first pass | [derek-lieu.com/start-here](https://www.derek-lieu.com/start-here) |
| — "Basic Game Trailer Editing Workflow" | The order of operations from capture to picture lock | [derek-lieu.com](https://www.derek-lieu.com/blog/2022/10/24/basic-game-trailer-editing-workflow) |
| — "The Simplest Trailer to Make For Your Steam Page" | The minimum viable store trailer for a small team | [derek-lieu.com](https://www.derek-lieu.com/blog/2021/4/18/the-simplest-trailer-to-make-for-your-steam-page) |

Lieu is a working game-trailer editor whose credits include Among Us,
Half-Life: Alyx, Dead Cells and Spelunky 2, and who publishes his method openly.
Where this repo states a trailer structural rule without another attribution, it
is his — practitioner experience, not a study.

## Methodology — product demo (service / app)

| Source | What it gives us | Link |
| ---- | ---- | ---- |
| Practitioner consensus across SaaS demo guides | Problem-first opening (lead with the pain, not the logo), the "moment it clicks" placed early, 60–180 s typical, completion falling sharply past 60 s | [contentbeta.com](https://www.contentbeta.com/blog/saas-demo-best-practices/) · [moonb.io](https://www.moonb.io/blog/saas-product-demo-video) |

**Caveat on this row.** Unlike the trailer and platform rows, this is aggregated
marketing-blog advice, not a primary source or a vendor rule. Treat the
*structure* as a useful default and treat the *percentages* those posts quote as
unverified — none of them publish their sample. `$video-brief` must not present
them as measured.

## Platform requirements

Read directly from the vendor pages on the date shown, not from third-party
summaries. **Third-party ASO blogs disagree with the vendors on several of these
figures** — the two caught while writing this file were "up to 3 preview videos
on Google Play" (the vendor allows **one**, plus XR extras) and "Google Play
requires 30–120 s" (the vendor states no duration requirement at all, only that
30 s autoplays). Both were caught by re-reading the vendor page, and by nothing
else in the process.

| Platform | Hard requirements | Strong recommendations | Link | Read |
| ---- | ---- | ---- | ---- | ---- |
| **Steam** | — | First store trailer primarily **gameplay from the player's perspective**; reach the action fast; logos and story beats later; in-game HUD visible is often a plus. The main trailer **autoplays silently** at the top of the page | [Steamworks — Trailers](https://partner.steamgames.com/doc/store/trailer) | 2026-08-06 |
| **Apple App Store** | **15–30 s**; up to **3 per language**; H.264 or ProRes 422 (HQ only); ≤ 30 fps; ≤ 500 MB; portrait or landscape (macOS/tvOS landscape only); **on-device capture only — must show only content within the app; no filming people interacting with a device, no over-the-shoulder, no fingers on screen**; suitable for all ages; must disclose if a shown feature needs IAP, subscription or login | Poster frame (default 5 s in) is what shows when autoplay is off — choose it deliberately. Plays **muted** by default, so carry meaning in on-screen copy. Show more gameplay than cutscenes | [Apple — App Previews](https://developer.apple.com/app-store/app-previews/) · [App Store Connect specs](https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications) | 2026-08-06 |
| **Google Play** | **One** preview video per listing (Android XR permits two more), given as a clean YouTube URL — not a playlist or channel, no extra parameters such as timecodes; monetization/ads **off**; public or unlisted; not age-restricted; embeddable | No stated duration limit, but **only the first 30 s autoplays, muted**. Core experience within the **first 10 s**; aim for **≥ 80 % representative footage** (limit title cards, logos, cutscenes); no fingers on the device unless usage is genuinely off-device; no black bars on portrait; captions recommended | [Play Console Help — Add preview assets](https://support.google.com/googleplay/android-developer/answer/9866151) | 2026-08-06 |

Apple's capture rule is the one that most often invalidates an otherwise-finished
cut, because it rejects the **footage** rather than the edit — an
over-the-shoulder shot cannot be fixed in the timeline. It belongs in the brief,
before capture, which is the whole argument for briefing video at all.

## Execution tooling

| Tool | Role | Note |
| ---- | ---- | ---- |
| [`browser-use/video-use`](https://github.com/browser-use/video-use) | Agent-driven editing: transcribe → pack → EDL → render → self-eval | MIT. **An external skill repository, not a Code Studios plugin dependency.** Its upstream installation instructions target Claude Code and are not used by this Codex plugin. Needs `ffmpeg` and an ElevenLabs API key (a paid call per source — gate it with `$api-cost-gate`) |
| [OBS Studio](https://obsproject.com/) | Capture | Free. The capture settings (resolution, frame rate, HUD on/off) are brief decisions, not editor decisions |

### What we take from video-use, and what we do not

We do not reimplement its editing helpers, and we do not restate its design
principles — its three (structured text surface with visuals on demand; ask →
confirm → execute → self-eval; a bounded re-render loop) are conclusions this
repo already holds, in `$spatial-audit`, `rules/autonomy-contract.md` (stop only at the enumerated conditions, otherwise write and report), and
`rules/self-loop.md` respectively. Worth knowing as convergent evidence; not
worth a second copy here.
