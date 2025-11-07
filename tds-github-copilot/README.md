# The Secret Life of a Tiny Assignment

_How a one-line task — “print the 10th prime” — revealed a semester’s worth of truths about AI, students and the quiet power of defaults._

---

It was a simple brief for hundreds of students using GitHub Copilot from the command line: **create `prime.py` that prints the 10th prime number**. That number is **29**. The logs they left behind — 138,811 lines of them — read like a backstage transcript of a modern classroom: which operating systems did the heavy lifting, which AI models actually wrote the code, and why something as small as a parallelization flag can slow an entire cohort.

Below is what we found about how real people and real machines get real work done.

---

## Act I — The Stage: Windows, Windows Everywhere

Before a single line of Python runs, the choice of operating system tilts the floor.

**OS sightings in the logs (share of ‘user-agent’ lines):**

```
Windows  617 ██████████████████████████████
Linux    286 ████████████
macOS    178 █████████
```

**Windows dominates.** That’s not just a preference. It shapes the kinds of problems students face: PATH issues, PowerShell quirks, backslash escaping. When you run a class at scale, **your biggest friction surface is the majority OS**.

**Actionable takeaway:** Ship a **Windows-first preflight** (PATH checks, `python` invocable, write permissions) and prefer **slash-agnostic** shell snippets. A 2-minute preflight saves a dozen support threads later that night.

---

## Act II — The Voice: What Model Students Actually Choose

Students saw catalogs boasting dozens of models. In practice, they gravitated to one family.

**Model selected per session:**

```
Claude Sonnet 4    195 ██████████████████████████████
Claude Sonnet 4.5   60 ████████
GPT-5                8 █
```

**Anthropic Sonnet 4 was the workhorse**, with 4.5 a meaningful second. Even when GPT-5 appeared in capabilities listings, it wasn’t the default choice for this task. Standardizing one model for a lab **reduces variance** and the “it worked for me, not for you” effect.

**Actionable takeaway:** **Pin a default model** per exercise unless you’re explicitly A/B testing. Fewer moving parts; better apples-to-apples learning.

---

## Act III — The Hidden Lever: Defaults That Quietly Slow Everyone

A small configuration traveled through the logs like a whisper:

**Parallelization flag in requests:**

```
executeToolsInParallel=false  244 ██████████████████████████████
executeToolsInParallel=true    ~0 (virtually none)
```

By default, tool calls ran **serially**. Creating files, verifying output, printing diagnostics — all queued up. On a single machine, that is merely a sigh. Across a class, it becomes a **collective slowdown** that erodes momentum and confidence.

**Actionable takeaway:** Where steps are independent, **flip parallelization on**. Faster feedback loops → more attempts → better learning curves.

---

## Act IV — The Hands: How Code Was Actually Written

Students converged on a correct solution, but the style — and micro-optimizations — told a subtler story.

**How they printed the answer:**

```
Direct print (print(find_nth_prime(10)))  35 ██████████████████████████████
F-string headline                          6 █████
```

**How they tested primality:** Most solutions looped all potential divisors up to √n. Only a rare few implemented **odd-divisor stepping** (skip even numbers after 2) — the easy, elegant speedup. In a lab this small, you won’t feel the runtime. But the habit of **recognizing constant-factor wins** is the point of teaching.

**Actionable takeaway:** **Reward micro-optimizations** in rubrics. A small “style & efficiency” nudge changes what students notice next time.

---

## Act V — The Tools: How Work Actually Gets Done

Behind the curtain, two tools dominated the choreography.

**Tool calls:**

```
str_replace_editor  560 ██████████████████████████████
powershell          395 ████████████████████
```

File editing bots (`str_replace_editor`) outpaced shell calls — a sign students leaned on automated edits rather than hand-rolled command lines. On Windows, PowerShell was busy…but also brittle when `gh` (the GitHub CLI) wasn’t installed or on PATH.

**Actionable takeaway:** Bake **“install & verify `gh`”** into preflight. Detect, fix, and move on.

---

## The Tally of Versions

**Copilot CLI versions (top 10 sightings):**

```
0.0.339  338 ██████████████████████████████
0.0.338  224 ████████████████████
0.0.337  210 █████████████████
0.0.336  120 ██████████
0.0.335   95 █████████
0.0.334   78 ███████
0.0.333   16 █
```

Seven versions in the wild is enough to produce “it broke after I updated” mysteries. When you teach at scale, **version sprawl is death by papercuts**.

**Actionable takeaway:** **Lock to one supported CLI version** per assignment and display it in the starter instructions.

---

## The Moment of Truth: Did It Print “29”?

The majority of runs got to a working `prime.py`. Where a **verification banner** was present — `=== EXECUTION VERIFICATION ===` — it concluded with the right number. But many sessions celebrated success narratively (“Perfect! … outputs 29”) rather than emitting a **machine-checkable signal**.

**Actionable takeaway:** Ship a tiny, uniform harness:

```text
=== EXECUTION VERIFICATION ===
29
```

No emojis. No headings. Just a line your grader can catch.

---

## What This Really Tells Us

- **The classroom is an ecosystem.** OS choice dictates setup risk; model defaults shape cost and consistency; flags you never see in slides shape speed.
- **Students follow the rails we lay.** If the rails enable parallel steps, success accelerates. If the rails encourage micro-optimizations, students learn to see them.
- **Measurement matters.** When success is narrative, improvement is guesswork. When success is a stable two-line banner, improvement is compounding.

---

## Quick Fix Kit (you can paste this into your course README)

1. **Preflight (Windows-first)**
   - Check: `python --version`, `gh --version`.
   - Create a temp folder and write/execute `prime.py`.
   - Normalize slashes in shell examples.
2. **Lock the stack**
   - One Copilot CLI version.
   - One default model for the lab.
3. **Speed up feedback**
   - Set `executeToolsInParallel=true` wherever steps don’t depend on each other.
4. **Grade what you want to teach**
   - Require a two-line **verification banner** that prints only `29`.
   - Award a small bonus for **odd-divisor stepping** or similarly clean constant-factor wins.

---

## The Five-Line TL;DR

- **Windows drives most friction**, so design preflight and shell snippets for it first.
- **Students mostly chose Anthropic Sonnet 4**, even when catalogs listed glossier options; pin a default to reduce variance.
- **Parallelization was effectively off**, slowing the entire class; turn it on for independent steps.
- **Verification was inconsistent**; mandate a two-line banner so graders (and students) get crisp, automated feedback.
- **Optimization is teachable**; reward the tiny tricks (odd-divisor stepping) that build engineering instinct.

---

Source: [ChatGPT](https://chatgpt.com/s/t_690dcd19bd4c81918c954039d1b7c033)
