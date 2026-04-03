# TDS 2026-01 Project 1 Analysis

<!--

cd ~/code/datastories/tds-2026-01-p1/
dev.sh -v /home/sanand/code/exam:/home/sanand/code/exam:ro \
  -v /home/sanand/code/tools-in-data-science-public:/home/sanand/code/tools-in-data-science-public:ro \
  -v /home/sanand/code/tdsnetworkgames:/home/sanand/code/tdsnetworkgames:ro \
  -v /home/sanand/code/datastories:/home/sanand/code/datastories:ro
copilot --yolo --model gpt-5.4 --effort xhigh
-->

You are analyzing student responses to the Tools in Data Science (TDS) course - specifically Project 1 for the Jan 2026 cohort.

Here is relevant content (and you can explore for more as you need):

- /home/sanand/code/tools-in-data-science-public/README.md for the course.
- /home/sanand/code/exam/src/exam-tds-2026-01-p1.js and /home/sanand/code/exam/src/exam-tds-2026-01-p1.info.js and the mentioned /home/sanand/code/exam/src/q-_.js files (and associated a-_.js files where relevant) for details.
- https://github.com/sanand0/tools-in-data-science-public/discussions for discussions related to these questions.
- /home/sanand/code/exam/dumps/tds-2026-01-p1.json for the raw data dump of all student responses.
- /home/sanand/code/tdsnetworkgames has the CloudFlare worker deployed at https://tds-network-games.sanand.workers.dev/ for q-network-game-\* questions.
- https://exam.sanand.workers.dev/filter?quiz=tds-2026-01-p1&email=&until=&limit=2000&page=0&history=1 for an API to fetch responses. history=1 fetches ALL submissions. email= is a student-specific email filter. page= and limit= are for pagination. Add positives=1 to filter only positive scores. See /home/sanand/code/exam/src/worker.js to understand how and when {total: -1} is assigned.

Analyze using the data-analysis skill.

- Save all code under ./scripts/
- Save downloaded data under ./data/ (.gitignore these - they should be reproducible)
- Save analysis under ./analysis/q-\*.md (.gitignore these - they should be generated and reproducible from the scripts)
- Save the pipeline in ./setup.sh - running this should reproduce all analysis from scratch, resuming from where it left off if interrupted.

Here are some things I'm curious about in general:

- This course lets students collaborate and hack. How much of each happened?
  - What led to the total: -1 for students? What's the story here?
- What's the story in WHEN students submitted their answers (history, final submission, effort, etc.)

Here are some things I'm curious about on specific questions.

**q-transcribe-numbers-server.js**, **q-markdown-parser-server.js**: How long and how many attempts did this take? Any useful, non-obvious insights?

**q-generate-\*.js**:

- Download and save all the generated images and charts.
- Compress the images into thumbnails of under 640px width and height preserving aspect ratio as avif with quality=30 using avifenc.
- What's the distribution of keys in their various responses? For example, what are preferred models? Datasets? Who has allowed publishing their email and who has not?
- What insights are there in the metadata of their generated images?
- What can we learn from the patterns of prompts? What features can we extract from the prompts? What's interesting in these?

**q-pr-merge-server**: Extract a dump of all PRs from answers.q-pr-merge-server where scores.q-pr-merge-server=1 - fetch from GitHub API the conversations and diffs and any other details.

- What were the repos they submitted to? Two repos dominate: https://github.com/lingdojo/kana-dojo and https://github.com/firstcontributions/first-contributions - which are intended for first, easy, merges, but what else?
- What's does the PR review/acceptance process for the major ones look like?
- What was the type of PR they submitted, e.g. typo fix, documentation update, code change, etc.? Were there any non-trivial PRs? Which ones?
- If we had to judge the value, e.g. public utility / contribution, of the PRs, what would be the top 5 contributions be and why?
- How long did PRs take to merge, across repos? What's the distribution, insight?
- Which PRs were auto-approved (e.g. bots, GitHub actions, etc.) and which were manually reviewed?
- Which PRs required the students to make edits vs which ones did not and were accepted as-is?

What other interesting questions can we answer from this data?

**q-share-secret-server.js**: Over 90% solved this! It's possible to get the source for this question and answer it. https://tds-hackkkkkkk.vercel.app/ is a public app that solves the question for any student.

- What's the distribution of the timing of these questions?
- Based on the GitHub discussions and timing of responses, who struggled, who hacked and how?
- What can we learn from this about how students approach problems, collaborate, and hack?

Be creative in your analyses. Here is one approach (you needn't stick to this) for creative ideas:

- Choose 3–5 distinct ordinary personas who would see this problem differently.
- For each persona, generate 3 diverse candidate ideas for analysis, different from what we've already looked at.
- List the 5 most obvious / conventional ideas across all candidates. Ban them, along with near-duplicates.
- Choose 2 unrelated domains. For each domain, extract 3 atomic structural rules. Use those rules to create 4 more ideas for this task.
- Merge all ideas removing overlaps. Keep the set maximally diverse across mechanisms, users, and time horizons.
- Critique each surviving idea: what assumption must hold, why it is non-obvious, why it may fail, and what makes it genuinely useful.
- Score each idea on impact, novelty, ease, and speed.
- Recommend 2 ideas: the best practical idea and the best wildcard idea, explaining why it beat the more obvious alternatives.

This is a long task and a long list of analyses. Don't analyze them right away.

- First, download the data you need and inspect it.
- Then create a detailed analysis plan. Double-check your plan - is it creative enough? Diverse enough? Interesting enough? Here is one way
- Then run just a few of the more interesting analyses, share the results with me, and get feedback.

If you get stuck anywhere (e.g. API issues, missing tools or files, environment access), stop and check with me. I'll give you access.

---

When saving analysis/q-\*.md files, make sure it aligns with an exact question.
Otherwise, just save in analysis/whatever.md.

---

Proceed with the plan and continue the comprehensive analysis.
Use sub-agents as required.

---

Deepen with more analyses. Use the data-analysis skill. Explore creative analyses (I mentioned earlier how you could do that).

Blow my mind. WOW ME with insights that Malcolm Gladwell would be proud of.

---

The q-generate-\*.js questions document how to evaluate each of the generated images using a prompt.

Write an agent-friendly CLI evaluate_images.py that evaluates each student's submission for these questions, saves the responses, and summarizes the scores.

- Search online for the latest Gemini API docs and use it.
- Use `gemini-3.1-pro-preview` as the model (Gemini 3 Pro is no longer available.)
- Use the GEMINI_API_KEY in .env.
- Scale the image to a max resolution of 768 x 768 before sending to the model.
- Each question mentions a prompt. Pass the prompt exactly as mentioned, along with the image, to the model.
- Provide the schema mentioned in the question as part of the input in the way Gemini API accepts schemas to force the API to respond in that format.
- Make sure the script is resumable, i.e. continues from where it left off if interrupted
- Allow running for a specific subset to make batch runs and parallelization easier
- Add a --force option to allow re-evaluation of specific students and/or questions
- Allow a --dry-run option
- Save all output in the .gitignored analysis/ directory - under a sub-directory - with a good naming convention for easy reference

Test run this for a few images and share your observations, suggest improvements, and wait for my input.

---

Create a ./gallery/ that has only the required files for publishing a gallery of thumbnails along with evaluations. This should include:

- The .avif thumbnails (640px) -- copy from data/assets/q-_/_-thumb.avif
- A summary.json with a `results` array of objects where each result has:
  - `email`, `question` (the primary keys)
  - `time` and `id` of latest submission before the deadline (see the .info.js file for deadline info)
  - `image_url`, `json_url` where we downloaded from
  - `submission` object which is the contents of the `json_url` we have downloaded
  - `response` from analysis/image-evals/gemini-3-1-pro-preview/results/q-_/_.json
- Include any other metadata you think would be useful for the gallery, e.g. question prompts, evaluation criteria, etc.

Run for 5 students x 4 questions. Ensure that the gallery file(s) are updated as you run. Estimate the total cost of running this.

---

In summary.json, reduce what's in .results[] to the minimum required. For example:

- Drop .evaluation and .paths - they don't seem important
- Move question_label to the top level to reduce duplication

Run for the all the students. Print the status an estimated time to completion as the script progresses and tell me how I can monitor it.

---

Stop the task. I will resume later.

---

Refreshing the summary each time is not required. Just generate the Gemini responses. We can generate the summary later. This will save time and reduce conflicts.

See if you can run a bit faster, e.g. via parallelization, sub-agents, etc.

---

summary.json is too large. See if there are ways to reduce the size in a way that will reduce the gzipped payload when served on a website. Don't over-optimize - we want to keep it reasonably easy to work with and understand. Consider the tradeoffs of different approaches and suggest the best one.

Also, add an "user" field the first 5 characters of the SHA256 hash of their email IDs (in lowercase). This anonymizes the email ID. Remove the "email" field for anyone who has not explicitly allowed sharing their email.

Based on this, re-build the summary.json and the gallery.

---

Re-include the evaluation outputs from Gemini in summary.json for completeness. That way, we remove the dependency on analysis/image-evals/gemini-3-1-pro-preview/results/.

---

Make sure summary.json includes all students who have submitted, even if their JSON/image is missing. In such cases, make sure that a script can easily identify what the gap is, e.g. via a "status" field with clear, discrete values.

Using `gh` create a GitHub release for each of these questions. Name the releases tds-2026-01-p1_q-generate-affective-chart, etc.
Upload the JSON and PNG (not AVIF/WEBP) files for each student's submission for that question as release assets.
Write a shell script to upload only unreleased assets (e.g. checking with `gh release view`).

---

<!--
/model claude-sonnet-4.6 (high)
-->

Create a dashboard of the scores of the students against each question in gallery/index.html.

Begin with a short paragraph explaining what this dashboard is. Link to https://exam.sanand.workers.dev/tds-2026-01-p1.
List the questions as bullets. Clicking on a question should open a popup that:

- Links to the question in a new window, e.g. https://exam.sanand.workers.dev/tds-2026-01-p1#hq-generate-affective-chart
- Shares the system prompt, user prompt, output schema (1 bullet each, derived from JSON, but make it human-friendly)

It should feature a table of scores. 1 row per student. The columns are below. On hover over column headers, provide a brief explanation of what the column is. Clicking on the column headers should toggle the sort by that column.

- ID (header rowspan=2): email where available, else the "user" hash.
- Time: time of the latest submission before the deadline, i.e. max(time) - friendly, local-timezone
- Affective Chart: (header colspan=6) has sub-columns. The sub-columns are labelled #, 1, 2, 3, 4, 5 and the values are below. We're trying to keep the column headers very compact and the tooltips provide the details.
  - #: overall_score
  - 1: compositional_intent.score
  - 2: constraint_adherence.score
  - 3. emotional_impact.score
  - 4. legibility_without_labels.score
  - 5. visual_originality.score
- Concept Incarnation: similarly
- Paradox Portrait: similarly
- Style Transplant: similarly
- Total: Sum of Q5-Q8 (single column, no sub-columns)

Use sticky headers so that the titles remain visible while we scroll. If this is not possible with tables, or tables will have poor performance, use grids or any other mechanism.

Clicking on cells should open a popup with details. There are 3 kinds of popups, and each is a well-designed mini-dashboard in itself with a consistent format and design across all questions and cells. The 3 kinds of popups are:

- Clicking on ID cell: shows all 4 thumbnails with submission details,
- Clicking on # cell: shows the thumbnail with submission details and the overall response (overall_score, and other question-specific fields, e.g. brief_met, exhibition_worthy, one_line_verdict)
- Clicking on 1, 2, 3, ... cell: shows the thumbnail with submission details and the response for that cell (score, reason, improvement)

In the popups:

- Hovering on the thumbnail should smoothly transition it to a max width/height of 640px or screen size (whichever is smaller) to allow them to see the details.
  - Link the thumbnail to the GitHub releases image so they can right-click and copy the image.
  - Clicking the thumbnail should open another popup showing the GitHub releases image. (Do not reflect this popup in the URL for bookmarking.)
- For submission details, show: prompt, model, dataset name linked targeting new window, insight, time of submission (friendly, local-timezone), link to question
- Show the score/overall_score prominently, along with a distribution micro-chart helping them understand where that score stands relative to others along with a rank

Make sure the table includes all students who submitted, even if their JSON/image is missing. In such cases, give them a score of 0 and make the cell visually distinct (based on the status field) to indicate the gap. The popup for such cells should explain the reason for the missing data and any relevant context.

Persist the state of the dashboard in the URL, e.g. via query parameters, so that they can share links to specific views. Sort order and the popup opened should be persisted. Avoid polluting history - use replaceState.

Allow the use of arrow keys to navigate the popups when they are open, e.g. left/right to move between columns, up/down to move between students, etc.

Below the table, include charts showing the distribution of overall scores for each question along with overall stats, e.g. number of submissions, average score, cost, etc.

At the end, include a brief description of the evaluation process. Include a button to see details that opens a popup which has the full evaluation process - based on prompts.md and past conversations.

Use well-guided sub-agent(s) to test adversarially to find errors in interactions (popups, keyboard navigation, hover, responsive design, sorting, ...) and design aesthetics. Fix what you find.

---

IMPORTANT: Because Claude will almost certainly stall when generating such a large file at one shot, you MUST break this into parts, generating the .html in chunks or layered edits (keeping each chunk small, max 100KB of edits) and saving it, checking it, then updating it with the next iteration, and so on.

---

- Improve the design. Use Claude's front-end design skill (search online if required).
- Use larger popups.
  - Show 640px width (responsive) thumbnails in the popup by default - no need to implement the zoom-on-hover.
  - Prompt, model, dataset, etc. can be to the left while the score and details can be to the right. Make sure the full prompt is displayed.
  - In the popup for `#` columns, no need to collapse the "All dimension scores". Always show them, along with their rank and normalized scores.
  - The layout could be: Thumbnail; below that, a row with [prompt, model, ...] on the left and [score, parameters, suggestion, distribution chart] on the right; followed by the table with dimension, score, rank, norm, reason.
- For each `#` column, calculate a normalized score fitting the column to a normal distribution. Show this in the popup. Also calculate the normalized total as the sum of the normalized `#` scores and add this as the last column titled "Norm". Run this calculation in the front-end.
- Instead of "Latest pre-deadline submission was not fetched..." say "No valid submission **before** deadline."

IMPORTANT: Because Claude will almost certainly stall when generating large edits at one shot, you MUST break this into parts, with small edits.

---

- Use front-end design skill to improve the parts outside the table. Make it look like a New York Times data story.
- In the popups:
  - Horizontally center the thumbnail
  - Increase #d-mini-dist svg width and height to 480 x 480, increase fonts a bit, with axes labels, and make this a proper chart. Enhance the chart to show more information (think about what additional information would be relevant)
- Clicking outside popups should close the (topmost) popup
- Modify the total to make it the sum of 0.75 x sum(overall_score scores of the 4 questions). That's because we told students that each question gets a maximum of 0.75 in the total. The highest "Total" should be <= 3 and the lowest should be 0. Document this in the tooltip for the Total column header.

---

<!--
/model gpt-5.x (xhigh)
-->

Resume the analysis.
Use the data-analysis skill.
Explore creative analyses (I mentioned earlier how you could do that) on the new data you have gathered about the generated images.
Be exhaustive. Blow my mind. WOW ME with insights that Malcolm Gladwell would be proud of.

---

Write a script to generate 4 CSV files named `analysis/q-*.csv` that contains one row for each `data/assets/q-*/*.json` and captures all the columns.

Include deeper insights on:

- Which image generation model to use (and avoid) for what
- How skills translate across questions (not just the image generation questions) and what insights can we gather from those - and what psychological, educational, or even philosophical theories do these strongly break or support?
- What Feynman would look for, and what he would find
- What Robert Cialdini would look for, and what he would find

---

<!-- /model claude-sonnet-4.6 (high) -->

Write comprehensive data stories about your findings, beginning with an index.html. Write like Malcolm Gladwell. Visualize like NYT. Use the data-story skill.

There are several findings. If you need to, create multiple HTML pages with different stories, all linked from index.html, do so. Link with clear signposting and navigation. Create shared CSS, JS, components, assets, etc. as needed. Use subdirectories as needed.

Use tooltips, popups, interactions, and animations as informative and engaging aids.

**Tooltips** are for:

- Context about non-obvious terms or phrases (only if relevant and useful)
- Additional context about references (where possible)
- Metadata and context about data points, table cells, chart elements, etc. (always)

**Popups** are for:

- Citations. Search for and include references. Cite the key point from the reference and link to it.
- Files. Link liberally to files as supporting evidence.
  - Clicking on file links should open the files in a popup, with a link to open the original in a new tab.
  - Syntax-highlighted if code
  - Show sortable for tabular data, gradient-coloring important numeric / categorical columns if that will help understand the context
- Data points. Provide extensive context for data points.
  - Wherever useful, clicking on data points, table cells, chart elements, etc. should open a popup that provides full context about that element.
  - Include narratives, cards, tables, charts, or even entire dashboards that answer what the user is likely to be curious about or wants to dig in for more details. E.g. context, examples, related metrics, trends over time, breakdown by relevant dimensions, etc.
  - Standardize the format of these popups so users know what to expect. Reuse popups by archetype.

**Animated SVGs** are for:

- Explaining processes, mechanisms, workflows, etc. The aim is to make users FEEL the process. One glance should give them an intuitive understanding of how it works, even before they read the accompanying text. Show how things are connected, what data flows from where to where, how elements, interact, etc.
- Guidelines: Use GPU-friendly rendering (transform, opacity). Sequence multiple animations deliverately. Respect `prefers-reducted-motion`.

Make it mobile-friendly (responsive, touch, ...), performance-friendly (e.g. lazy loading, requestAnimationFrame, ...), keyboard-accessible.

IMPORTANT: Because Claude will almost certainly stall when generating such a large file at one shot, you MUST break this into parts, generating the .html in chunks or layered edits (keeping each chunk small, max 100KB of edits) and saving it, checking it, then updating it with the next iteration, and so on.

---

Overall, increase the depth of analysis and storytelling. Mention what psychological, educational, or even philosophical theories do these strongly break or support. Mention what practical takeaways for students and educators are.

- In some stories, the article body is too close to the hero section - increase vertical spacing. two-labor-markets.html is fine. endgame.html, two-exams.html, model-playbook.html, social-infrastructure.html needs spacing
- In model-playbook.html
  - "No model wins every brief" chart - model labels that are rotated 45 degrees go into the table and are hidden. Fix the positioning
- In two-labor-markets.html
  - Link to the actual 5 PRs in the long-tail market and explain what exactly the PR did and why it's valauble. Include stats on the number of human-to-human discussions, commits, lines of code changes, etc. for each PR.
  - Use consistent color coding for sink repos vs long-tail repos across all charts and mentions.
- In social-infrastructure.html
  - Link to the public decoder: https://tds-hackkkkkkk.vercel.app/
  - Take a look at the GitHub discussions for this question, where the late contributors were STILL discussing how to solve it and comment on that behaviour
- In endgame.html:
  - How does the archetype impact performance?

Fix tooltip positioning. The tooltips appear with their CENTER at the current mouse position. Instead, the bottom tip is what should be at the mouse position. Also, make sure the tooltip doesn't go off-screen.

For every chart element, add informative tooltips (they should be truly useful - not just info dumps).

---

Link extensively at every opportunity - e.g. to GitHub discussions, original sources for concept/law/effect/theory/... references, etc.

In endgame.html keep in mind that server-validation errors are usually students trying to HACK the server (which is encouraged)! It's not a server side mistake. Reword that section accordingly.

Also: From index.html include a card (as the sixth one) linking to gallery/ and explain what it is.

<!-- copilot --resume=fff49a52-d237-4f56-b2f7-27af4ebfbc60 -->
