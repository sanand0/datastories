# Prompts

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
