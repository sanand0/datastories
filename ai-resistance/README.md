# AI Resistance

On 16 Nov 2025, I prompted [Claude Code](https://claude.ai/code/session_017fvgqpauYsPANLpyqS6v7Q) to:

> Download and read the paper at https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5560401
>
> Specifically, find the data for Figure 4. Moral Repugnance vs. Technical Feasibility (you may need to fetch it from GitHub or other sources - explore ALL avenues!!)
>
> Save the data under ai-resistance/ as CSV or JSON files.
>
> Then create an interactive scatter-plot similar to Figure 4 in the paper in ai-resistance/ to view as a web app.

This did a good job. So, I continued:

> Write a New York Times style scrolly-telling data story based on the paper around this interactive chart.
>
> Modify the chart so that that brushing the chart will list the items selected inside the rectangle alongside the chart. That lets users pick a region and try to understand what exactly is inside it.
>
> Selectively highlight different parts of the chart as the user scrolls down the page, explaining what is interesting about each part.
>
> Write the story as a Malcolm Gladwell-style narrative with a compelling hook (human angle, tension, mystery), story arc (build narrative through discover, reveal insights progressively), concrete examples and evidence woven in (search the paper or online), "wait, really?" moments (surprising findings), "so what?" (implications and actions), and honest caveats (limitations).
>
> Also document the process you followed to extract the data in the story.

There were some issues:

> Move ai-resistance/scrollytelling.html to ai-resistance/index.html and ai-resistance/index.html to ai-resistance/chart.html
>
> Delete ai-resistance/paper-pdf - we don't need that. Instead, link to the paper's source directly wherever relevant.
>
> Take a screenshot of just the chart as an 8-color optimally compressed ai-resistance/screenshot.webp and update config.json with details.

[Here is the result](index.html).
