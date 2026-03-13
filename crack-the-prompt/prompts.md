# Prompts

## Blog post (Copilot yolo - sonnet-4.6 medium)

An effective way to solve online exams is to point a coding agent at it.

For [PyConf, Hyderabad](https://2026.pyconfhyd.org/), my colleague built a [Crack the Prompt](https://crack-the-prompt.straivedemo.com/) challenge. Crack it and you get... I don't know... goodies? A job interview? Leaderboard bragging rights?

I told Codex:

> Use the browser to visit https://crack-the-prompt.straivedemo.com/ and solve it using the email ID root.node@gmail.com and GitHub handle sanand0

It analyzed the site, even spawing sub-agents, to solve the challenge.

The session logs are extracted into session-*.md in this directory.

### Randall Munroe - suffix

Write a short blog post about the process Codex went through to solve the challenge, and the implications, written in Randall Munroe style, in randall-munroe.md.

### Matt Levine - suffix

Write a short blog post about the process Codex went through to solve the challenge, and the implications, written in Matt Levine style, in matt-levine.md.

### Richard Feynman - suffix

Write a short blog post about the process Codex went through to solve the challenge, and the implications, written in Richard Feynman style, in richard-feynman.md.

### Malcolm Gladwell - suffix

Write a short blog post about the process Codex went through to solve the challenge, and the implications, written in Malcolm Gladwell style, in malcolm-gladwell.md.

## Story (Copilot yolo - sonnet-4.6 high)

Create a landing page, index.html, that explains the challenge, briefly describes the process Codex went through.

This directory will be deployed on GitHub at https://github.com/sanand0/datastories/ under the crack-the-prompt/ and will be visible at https://sanand0.github.io/datastories/crack-the-prompt/ .

Document (via cards) the blog posts and session logs. Clicking the card should open the .md file in a popup, rendered with markdown formatting and syntax-highlighted. If any of the content can benefit from formatting (e.g. JSON), feel free to modify the .md files to improve the formatting.
