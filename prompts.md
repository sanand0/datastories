# Prompts

## Update summary and keywords, 23 Apr 2026

<!--

cd /home/sanand/code/datastories
dev.sh
copilot --yolo --model gpt-5.4 --effort high

-->

Go through what you need in each data story and update config.json with retrieval-friendly metadata for it by adding these keys:

- "summary": "...",
- "keywords": ["...", "...", "..."]

Rules:

- "summary" must be 1 sentence, 20-40 words.
- Write the summary as the single best takeaway or message of the content, not as "This article/talk/slides are about..."
- Make it useful for semantic search: include the problem, method, idea, or conclusion if relevant.
- "keywords" must be 4-8 short topic phrases someone might search for.
- Keywords should be specific, noun-phrase style, lower-case, and non-overlapping.
- Do not use vague tags like "technology", "business", "presentation", or "data".
- Do not mention formatting, tone, or that this is a summary.
- Base the output on the full content, not just the title or opening.

<!-- copilot --resume=4b3f7a0c-0ddd-40e8-99db-9da441177382 --yolo -->
