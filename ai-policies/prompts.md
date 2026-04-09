# Prompts

## University AI policies, 3 Apr 2026

<!--
Research: https://chatgpt.com/c/69cf42a9-ed04-839b-bdf1-e010677d81c7

cd ~/code/datastories/
dev.sh
claude --yolo   # --effort high
-->

Use the data-analysis skill to analyze the university Gen AI policies in ai-policies/university-genai-policies.json.

Narrate the insights using the data-story skill and generate ai-policies/index.html. Write like Malcolm Gladwell, visualize like the New York Times. The aim is to

- Explain how universities are approaching AI
- Share the contrast, what's unusual (outliers), consensus, etc.
- Dig into what's NOT being said, what's conspicuously absent, etc.

Include a sortable table with:

- rows as universities (link to policy)
- columns as policy elements (click headers to sort)
- cells as colored policy elements summarizing the stand, with a popup explaining the full detail, with citation, linking to the source, etc.

Use links, tooltips and popups extensively.

- Links liberally to external sources - not just the policy documents, but also related news articles, research papers, etc.
- Tooltips for non-obvious terms or phrases (only if relevant and useful), additional context about references (where possible), and metadata and context about data points, table cells, chart elements, etc. (always)
- Popups for citations (evidence, quotes), data points, etc.

---

The JSON now has 5 new universities. Analyze these and incorporate the findings:

- Princeton University
- Stanford University
- University of Sydney
- The University of Hong Kong
- University of Toronto
- Imperial College London
- London School of Economics and Political Science
- The University of Melbourne
- UNSW Sydney
- The University of Tokyo

This may need a rewrite of the story, which is OK. Don't make this look like a revision of the previous story.
Ensure that it feels like a whole story, not a patchwork of old and new.
Review everything with a critical eye, and rewrite as needed to ensure it flows well and is engaging.

Make sure the policy table occupies the full width of the screen.
Keep cells compact and wrapped, i.e. badges, use the TD's background directly.
For University, just include the flag and the Uni name. On hover, show details like #UA #1 QS 2025, etc.
The entire table should fit comfortably in a 1920px wide screen.
Move the table up between Part Two and Part Three

In the popups, "Read source policy" seems the same as "View policy document". If that's mostly true, maybe drop one?

End with takeaway cards.

This is a complex task.
PLAN. Then execute against a checklist. Then VERIFY.

---

Allow .three-yes to occupy a wider width - or make them one below the other. It's too narrow.
Move "10 Things No Policy addresses" above Part 5.

Research online for more best practices on AI policies and incorporate commentary / takeaways based on that, interspersed with the findings.
Be thoughtful and critical in the analysis, and don't just report on the data - interpret it, find the story, and tell it in an engaging way.

Update README.md and config.json with the ai-policies/ data story and screenshot.

---

I have more universities' data in harvard_plus4_genai_policies_rigorous.json.
Merge this into university-genai-policies.json.
Make sure all tables, charts, etc. include the new universities.
Incorporate any new insights or corrections.
Don't make this look like a revision of the previous story. Ensure that it feels like a whole story, not a patchwork of old and new.

<!-- claude --resume 4a1b4bc1-b51e-4f72-a7dc-bd1c5443eb6a -->
