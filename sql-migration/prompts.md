# Prompts

## Generate data

<!-- https://chatgpt.com/c/69a14b8e-5cd0-839e-937a-3d065c87bbf1 -->

I'd like to create a demo of the process with which we use LLMs and coding agents to convert Microsoft SQL Server scripts, that is MSSQL scripts, to MySQL. The objective of this demo is to explain to clients the workflow, the benefits, the impact, the logic, etc. For this, generate a synthetic dataset of about 100 scripts of varying complexity in MSSQL. Then, convert these into the corresponding MySQL variations. Create a realistic synthetic log file of execution over a month, which illustrates which of these MSSQL queries have been executed, when, how often, and the approximate execution time for these queries, and any other typical metadata that is associated with these logs, such as who ran these queries or any other things that you think would be relevant. Along with these metadata files, include any other piece of information that you think will be useful for such a demo.

Create a synthetic dataset pack, consolidate it as a zip file, and allow me to download it.

## Visualize demo (Codex)

<!-- /home/sanand/.codex/sessions/2026/02/27/rollout-2026-02-27T16-03-27-019c9e1f-c29d-7a00-87f0-b9d6a6c3760c.jsonl -->

This directory has a sample dataset for Microsoft SQL to MySQL conversion scripts. We want to create an interactive HTML demo as a rich single-page application that explains the process of how we use LLMs to convert the SQL Server scripts to MySQL. To do this, create a narrative data story in which we begin by showing a nice data visualization with each of these scripts represented as little circles or squares or whatever, categorized in a variety of different ways, and use an animated sand dance transformation to show how the scripts are grouped together. For example, what are the different kinds of tables that they're using, how often are they executed from a frequency perspective, what is the purpose of different scripts, etc., allowing the user to get a feel for the underlying data. Then explain the nature of the problem, the business impact that it has when these scripts from a performance perspective are not optimal, the need for migration, the typical cost of manual migration, the kinds of problems that migrations would cause, etc. And ideally, I would like a simulation where the user can move around some slider or the other to see under different circumstances what the business impact of the migration might be. You may consider, for instance, using sliders for the volume of queries that need to be migrated, the... Quality factor and how that impacts both conversion factors and business outcomes, and so on. Then, explain a process by which we convert, using LLMs, the SQL Server scripts into MySQL. I'd like a set of cards from left to right that explain the process, where clicking on each of these cards below shows a nice, rich infographic that illustrates what's happening in each of those steps. Make the illustrations as animated SVGs so that the user will get a sense of what is happening just by looking at the animation, rather than even having to read the description of what we're doing in each step. Now, keep in mind that this process must factor in how to reliably convert SQL scripts. So you need to think about whether different strategies will need to be applied for different scripts, whether you need verification, if so, how can we run that verification, how can we do corrections on top of this, should we generate test cases, should that test case require synthetic data? All of these things should be factored into the process. I'm looking for something along the lines of maybe a six-step process that you can demonstrate. Then what I'd like you to do is show one or two sample scripts being converted. Show specifically on the left the original script, the output on the right side, and I'd like you to find ways of mapping the original to the target and share non-intuitive, non-obvious insights about how this worked. Also, make up a synthetic but realistic. example of how the processes, that is the six steps in the process, were actually applied to this one or these two scripts to get to the outcome. Make sure that the narrative that accompanies this gives a clear sense to the user of how LLMs can, from a business perspective as well as from a technical perspective, help the migration of SQL scripts, but while doing this, also ensure that you flag off the caveats in such a process.

### Edits

Edits for Act 1:

- Clicking on a SQL query should open a popup with rich details about
  - Metadata (e.g. risk, table family, etc.)
  - The original query
  - The converted query
  - A side-by-side diff view of the original and converted queries, with syntax highlighting and line numbers.
  - Any other available information you think will be useful

Edits for Act 5:

- Add syntax highlighting to the code.
- When hovering over the mappings, highlight (e.g. via a different background color) the relevant code snippets in the source & target code.
- Ensure that the source and target code have a minimum height that covers the entire .code-panel vertically.
- Add one more example to the existing two examples. Pick something that illustrates a different point than the existing two examples.

Move Act 3 below Act 5

### Fix errors

Fix this console error:
sql.js:693  Uncaught ReferenceError: module is not defined
(anonymous) @ sql.js:693

Though syntax highlighting exists in the DOM, they ALL seem to be .line-code. Some problem there.

Renumber the acts sequentially.

There's a scrollbar on EACH long line in the source. Make sure only the whole code block has a scrollbar, not each line.

Include an explanation of what dataset was provided as an input for this migration as part of Act 1.

Highlight the non-obvious challenges, e.g. "preserving numeric precision and JSON path typing", "MySQL has no direct MERGE equivalent", etc.

### Tweaks

In Act 1, Move the "Input Dataset" and "Non-obvious challenges" below the visualization instead of on the right.
Change "Runtime share by purpose" to "Queries by purpose" and when we click on table family, etc. redraw with "Queries by table family", etc. Also update the "Hotspot signal" based on the selection.

## Update docs

Update README.md explaining what this demo is about. (It already documents the synthetic dataset. See `prompts.md` and explain how it was generated.) The aims is that a person reading the README should instantly understand what the demo is about, what the dataset is, and how it functions. Also include a "Setup" section that crisply documents how to run this demo.
