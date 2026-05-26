# Prompts

## Add process, 26 May 2026

<!--
cd /home/sanand/code/datastories/
dev.sh -v /home/sanand/code/private-research/wikipedia-parquet:/home/sanand/code/private-research/wikipedia-parquet \
  -v /home/sanand/code/scripts:/home/sanand/code/scripts:ro
claude --dangerously-skip-permissions
-->

I would like you to extend `longest-wikipedia-string/index.html` at the bottom with details on the process by which the analysis was done, including downloading the dataset, using the `pylcs` library to find the longest common substring, how it was optimized, etc.

The code is in `/home/sanand/code/private-research/wikipedia-parquet/` and you should also check the Codex logs at `~/.codex/sessions` to understand how I prompted it (quote as required; also see the prompts.md in that directory) and how Codex did the job. `/home/sanand/code/scripts/agentlog.py` could help you parse the Codex logs into Markdown. The session ID is `019e61da-237d-7b40-859b-b77a63515ab8`.

Explain it that to a layman in a way that helps them understand how AI coding agents can be used to analyze such large datasets effectively.

---

Extensively link the sections you added. For example, link to Codex, GPT-5.5, the HuggingFace Wikipedia Parquet dataset, the pylcs library, and any other relevant tools or concepts. Use hyperlinks to make it easy for readers to explore these topics further.

Place the Step 1 ... 5 cards in a wide container that occupies the full screen width, wrapping them as needed for smaller screens, centered.

Use animations to compare the speed benchmark between the four methods. Make sure it's visceral and the users can understand the difference. Feel free to include illustrations as required.

Explain the different approaches for a layman: what is fingerprinting, how does BLAKE2b hashing work, etc. Include small illustrative code snippets (with syntax highlighting) to help explain these concepts and how they are used.

<!-- claude --resume 53294834-ccc7-4046-adb1-de647609e779 --dangerously-skip-permissions -->

## Initial story, 26 May 2026

<!--
cd /home/sanand/code/datastories/
dev.sh -v /home/sanand/code/private-research/wikipedia-parquet:/home/sanand/code/private-research/wikipedia-parquet
claude --dangerously-skip-permissions
-->

See `/home/sanand/code/private-research/wikipedia-parquet/prompts.md` which created `/home/sanand/code/private-research/wikipedia-parquet/lcs.md`
listing long strings that appear across many distinct English Wikipedia articles.

Write an interesting data story about it as a standalone `longest-wikipedia-string/index.html`.

Here are some things that I would consider interesting: that there is a Wikipedia parquet dataset that are small as about 35 gigabytes, and the structure and schema that it has is interesting in itself. This is documented in `wikipedia-parquet/schema.md`.

It's also interesting that there is one long string that totally stands out, which is the minor planet discoveries that appears across several articles labeled meanings of minor planet.

Many of the repetitive strings are repeated across structured Wikipedia articles, though - like different senates, different municipal corporation wards, different alphabets of the letter for iron cross recipients, different tunneling companies, etc. But some are a little more diverse than that. For example, Jangipur subdivision appears across a variety of different towns, which are reasonably related, but at least are named differently. The article about hill forts is distributed across several hill forts and is also slightly more diverse. The article about the 19, sorry, 1898-99 season in football is spread across some fairly diverse individuals that seems interesting. So also the list of elements.

So you get a sense that the more diverse the articles are in which a common string is present, the more interesting it becomes.

Explore different angles. Ideate & plan by diverging widely, then converge by critiquing and scoring your ideas. THEN, write the story. Feel free to use the underlying data - e.g. for further analysis or crafting references and so on.

Create an interesting story that is newspaper-worthy. Fact-check with external references, research online, link and cite liberally.

---

Expand the "Five Stories ..." cards by default.
Add more links to Wikipedia articles littered around the narrative.
Make the narrative more scannable by **highlighting key points**. Scanning the key points should give a good sense of the story, even if you don't read the whole thing.
Make the "Diversity Spectrum" chart occupy the full screen width, standing out.
Allow dark and light mode toggles - ensuring that ALL text contrasts well in both modes. (You'll probably want to compare the computed resulting colors and backgrounds and/or use screenshots.)

---

Update ./config.json. Include the newly added longest-wikipedia-string/screenshot.avif

<!-- claude --resume 69d79148-7491-4511-9d50-728102331b54 --dangerously-skip-permissions -->
