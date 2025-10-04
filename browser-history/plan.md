# Browser History Story Idea Plan (updated 2025-10-04)

## Data Snapshot (Edge History, Jul 13 – Oct 4, 2025)

- 97,573 recorded page visits covering 84 days; activity spans Jul 13 09:09 UTC to Oct 4 02:01 UTC.
- Communication-heavy browsing: mail.google.com (~16.5k visits), calendar.google.com (~7.2k), meet.google.com (~2.7k).
- Strong maker footprint: github.com (~8.3k visits) and localhost endpoints (~5.9k total) indicate active development/testing flows.
- AI assistants are embedded in workflow: chatgpt.com (~6.0k visits) and aiStudio (~170) alongside research-heavy search terms.
- Daily rhythm: weekdays average 1.2–1.4k visits; weekends drop to ~0.8–1.0k. Hourly peaks between 05:00–15:00 UTC, near-zero activity after 19:00 UTC.
- Search curiosity: top queries cluster around AI benchmarks, creative coding (“10 print chr$(205.5+rnd(1)); goto 10”), media references, and tooling filters (e.g., `path:**/agents.md`).
- Deep work bursts: 1,663 sessions with ≥10 visits under 5-minute gaps; 162 “marathon” chains (≥120 visits) up to ~2 hour spans.

## Candidate Story Ideas & Evaluations

### 1. Inbox vs. Maker: Visualizing Digital Context Switching

- **Concept**: Quantify how each workday oscillates between communication surfaces (Gmail, Calendar, Meet) and builder zones (GitHub, localhost, AI sandboxes). Narrate how a knowledge worker negotiates reactive vs. proactive time.
- **Analysis**: Categorize domains into communication, development, AI co-pilot, publishing, learning. Summarize daily/weekly shares, identify days with dominant modes, and surface context-switch spikes around meetings.
- **Visual**: Stacked stream or braided ribbon per day showing mode share; annotate notable spikes with search topics or significant meetings. Ground story in people-centric framing for approachability.
- **Evaluation**: Novelty – Medium/High (personal telemetry plus domain classification); Visual Impact – High (braided ribbons draw clear contrasts); Usefulness – High (readers see tangible tactics to reclaim maker time); Reliability – Medium (domain taxonomy manual—needs documentation & spot checks per verification guidance).

### 2. Flow Sprints: Mapping Marathon Browser Sessions

- **Concept**: Treat the 162 multi-hour browsing “sprints” as episodes of deep focus. Explore what topics dominate these bursts and whether AI, coding, or research fuels them.
- **Analysis**: Detect clusters by session length; overlay key domains and search terms per sprint; contrast weekdays vs. weekends and pre/post lunch timing.
- **Visual**: Timeline ridgeline where height = visits per minute and color encodes sprint theme; small multiples echo hand-drawn diaries for intimacy.
- **Evaluation**: Novelty – High (few public stories dissect personal browsing sessions at this granularity); Visual Impact – Medium/High (flow ridgelines with annotations of search snippets); Usefulness – Medium (inspires readers to audit their own focus rituals); Reliability – Medium (session detection sensitive to Edge logging gaps—needs transparency).

### 3. Curiosity Atlas: What Search Terms Reveal About 2025 Obsessions

- **Concept**: Cluster 20k+ search terms into themes (AI benchmarks, media fandom, slidecraft, job impact anxiety) to show intellectual wanderings over three months.
- **Analysis**: Normalize search terms, group via keyword clustering, trace weekly volume to see news-cycle reactions; pair with downstream behavior (which domains followed the search).
- **Visual**: Tile-map atlas or hand-drawn-esque legend referencing personal data postcards to keep tone playful and reflective.
- **Evaluation**: Novelty – Medium (search-term stories exist, but thematic clustering plus follow-through adds depth); Visual Impact – High (color-coded atlas with annotated quotes); Usefulness – High (readers glean zeitgeist of AI-age curiosity); Reliability – Medium (Edge history omits mobile/private sessions; note scope limits and anonymization strategy).

### 4. Favicon Loom: Turning Browser Exhaust into Mosaic Art

- **Concept**: Reinterpret the “Iconic History” favicon tapestry with current Edge data, highlighting how productivity, AI, and entertainment interleave. Compare weekday vs. weekend mosaics.
- **Analysis**: Export visit chronology, map favicons, color by domain clusters, and compute entropy (diversity) scores to anchor visuals in quantitative insight.
- **Visual**: Animated grid or scrollytelling mosaic evolving hour by hour, nodding to precedent art pieces that translate history trails into imagery.
- **Evaluation**: Novelty – Medium (builds on prior art but updates for AI/remote-work patterns); Visual Impact – Very High (mosaic instantly shareable); Usefulness – Medium (leans artistic; supplement with explanatory captions); Reliability – Medium/Low (favicon availability inconsistent; ensure reproducibility notes & open-source code).

### 5. Circadian Stack: The Remote Worker’s Clock, Through Edge

- **Concept**: Turn hourly visit density into a chronobiology story—highlight early-morning spikes, afternoon drop-offs, and near-zero late-night activity, speculating on time-zone juggling.
- **Analysis**: Normalize hourly counts per weekday, compare to meeting-heavy tools vs. maker tools, annotate notable deviations (launch days, travel prep on Agoda).
- **Visual**: Circular heatmap or layered day/night bands leading readers from macro (24-hour cycle) to micro (one emblematic day). Pair narrative with reminders that data stories serve people first.
- **Evaluation**: Novelty – Medium (time-distribution pieces common, but domain overlay distinguishes it); Visual Impact – Medium/High (radial clock draws attention); Usefulness – High (helps readers reflect on their own remote routines); Reliability – High (hourly buckets robust; still clarify UTC vs. local assumptions and missing-device caveats).

### 6. AI Co-Pilot Reliance Tracker

- **Concept**: Quantify interactions with AI assistants (ChatGPT, Gemini/AI Studio) vs. traditional resources (Google search, StackOverflow, GitHub issues). Examine how AI usage coincides with development sprints or ideation bursts.
- **Analysis**: Tag visits to AI tools, track session context, correlate with spikes in GitHub/localhost activity and search queries about benchmarks/outcomes.
- **Visual**: Sankey linking precursor searches → AI assistant visits → downstream implementation pages; annotate with mini-case studies of specific projects.
- **Evaluation**: Novelty – High (rare quantified narrative on day-to-day AI reliance); Visual Impact – High (storytelling Sankey/annotated flow); Usefulness – High (audience curious about practical AI adoption patterns); Reliability – Medium (requires careful disambiguation of open tabs and user accounts; document methodology and privacy safeguards).

## Next Analytical Steps

- Document assumptions: domain categorization, timezone inference (UTC vs. local), and data gaps (mobile/private browsing) before visualizing.
- Build reproducible notebooks with read-only SQLite access, ensuring raw data never published—aggregate only.
- Prototype visuals with lightweight datasets, gather feedback on narrative clarity, then iterate for publication.
- Plan privacy review: blur or aggregate sensitive URLs/titles; obtain consent for any screenshots.

## Publication Notes

- Anchor narratives in personal voice while situating patterns in broader cultural context (AI adoption, remote work), per data storytelling best practice.
- Pair each story with methods box and downloadable summary stats to bolster transparency.
- Consider pairing the mosaic/artistic pieces with more analytical charts for balance.
