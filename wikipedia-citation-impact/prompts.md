# Prompts

- ChatGPT ideation: https://chatgpt.com/c/6a12c717-ff40-83ec-980d-7cbd10f19f8b
- ChatGPT visualization: https://chatgpt.com/c/6a177d20-d0f4-83ec-a17c-6aee4f5a1355
- Claude visualization: https://claude.ai/chat/083473fc-ec72-496d-9487-57bd1c3610f8

## Initial version, 28 May 2026

<!--
cd /home/sanand/code/datastories
dev.sh -v /home/sanand/code/private-research/wikipedia-parquet/:/home/sanand/code/private-research/wikipedia-parquet/:ro
claude --dangerously-skip-permissions
-->

Write a data story about the impact on Wikipedia pages of a domain vanishing or removing all its links in the style of Randall Munroe.

Randall Munroe: Applies rigorous physics and engineering to absurd hypothetical questions with deadpan seriousness; stick-figure diagrams as essential explanatory tool; dry humor emerging from taking silly premises to logical extremes; "Thing Explainer" constraint of simple words forcing creative clarity; footnotes and asides deliver jokes; treats reader curiosity as worthy of real scientific effort regardless of question's absurdity.

The original idea came from exploring the Huggging Face Wikipedia structured dataset at https://huggingface.co/datasets/wikimedia/structured-wikipedia. You can see the ideation and analysis origation at `/home/sanand/code/private-research/wikipedia-parquet/chatgpt-ideation.md` where ChatGPT suggested a "citation collapse simulator".

I followed up on this idea and wrote the prompt in `/home/sanand/code/private-research/wikipedia-parquet/prompts.md`. Read the session details from the codex logs for the session ID `019e69df-6770-7ba1-a247-494a6747b6ab` (perhaps using `/home/sanand/code/scripts/agentlog.py md 019e69df-6770-7ba1-a247-494a6747b6ab`) to understand how it analyzed the dataset.

The result is in `/home/sanand/code/private-research/wikipedia-parquet/citation-impact.csv`. We have the impact on Wikipedia of removing an entire domain.

I also had Claude create a `/home/sanand/code/private-research/wikipedia-parquet/citation-impact.html` with a treemap that visualizes the damage of removing each of these 500 domains. The prompt used there was:

> Visualize this citation impact spreadsheet as a single-page HTML treemap. Each row is a domain and should represent a cell. The size should be based on the Any column, which is the second column. Add a slider to select the color based on any of the remaining columns, ranging from 5% to 100% in steps of 5%. If the 30% column value is chosen, then color based on the ratio of the 30% column value divided by the Any value. Use a linear D3 color scale. Scale colors to the bounds of the ratio in each column.

Looking at the treemap, a few things stand out. Firstly, archive.org clearly dominates the entire space as the single largest linked domain by far, though it's interesting that google.com is pretty high up on that list as well. However, the percentage of pages that would be left with no citations if we removed archive.org is not that high. That comes from the 100% column in the CSV file. Only about 9.8% of pages are left completely without a reference if archive.org vanished, but stat.gov.pl has a much stronger impact. Almost 83% of the pages that it is mentioned in mention only stat.gov.pl. The number is pretty high for biolib.cz, marinespecies.org, portsreference.com, etc.

I also added a `/home/sanand/code/private-research/wikipedia-parquet/citation-impact-domain-categories.csv` that categorizes these domains into a "source" (higher level category) and a "taxonomy" (granular - independent of source, not a sub-level).

As part of the story, include versions of this treemap that allow the user to move the slider and get a feel for the level of impact on pages. Explain with narratives for different levels where you find an interesting story.

When incorporating the treemap from `citation-impact.html`, you can ignore the headers, style, and the font, etc., but the structure of the treemap and the controls in the HTML file can be preserved. You should also modify it to allow categorizing, that is, grouping the boxes together based on source and on taxonomy independently. So the user can choose between no categorization or categorized by source or categorized by taxonomy, and the boxes should move smoothly. In each of these cases, the size based on the any column should be the sorting criterion.

Use the data-story skill. Think like a journalist. Focus on the most interesting stories that emerge from the data. That make the reader say, "Huh, that's interesting!"
Write in Randall Munroe's style. Visualize like the New York Times.

Generate this as single page `./wikipedia-citation-impact/index.html` that embeds what you need from the CSVs.

---

I think you tried using playwright but weren't able to. What did you try and what happened and how can I fix it?

---

Include EXTENSIVE links to Wikipedia and any other source at every opportunity.
Allow dark and light mode toggle.
Allow .full-bleed to take up the full page width. No need for max-width.
Currently, we have 4 cards in a row and they wrap into 3 + 1. This happens in two places. Maybe include these inside a .full-bleed or equivalent, centered?
Maybe allow the .compare-table to take up full width, centered, as well? The "Category" column wraps too much and we have far more lines than required.
The treemap color scheme doesn't look good. Specifically, the contrast is low. Prefer more vibrant colors and wider range of colors. Maybe scale from min to max? The original citation-impact.html had a color scheme that I liked. You don't HAVE to use that, but if you change it, make sure yours is better.
Use CDP at localhost:9222 with Playwright to test.

---

The blue in the treemap is TOO strong! Is there a better palette with good contrast? RdYlGn maybe? Or just Reds? Or even the original palette in citation-impact.html? In any case, make sure the text is always clearly legible in dark/light modes.

<!-- claude --resume 47869b7c-e1f3-48c3-aeb6-70bc43ccfd07 -->

---

Update README.md and config.json with wikipedia-citation-impact/{index.html,screenshot.avif}.

<!-- claude --resume ed9e53b1-bfd6-40ca-9dd6-dc25032b06ea -->
