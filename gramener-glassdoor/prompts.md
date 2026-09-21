# Prompts

## Update data, 21 Sep 2026

<!--
cd ~/code/datastories/gramener-glassdoor/
dev.sh -- codex --yolo --model gpt-5.6-luna --config model_reasoning_effort=medium
-->

Update glassdoor.json with any new / updated information from Glassdoor since the last time we have data for.
Write a script that will do this. Ensure that it's idempotent and resumable and don't lose any existing data.
See existing code and prompts for reference.
Run and test.

--- <!-- steering -->

I've logged into the employer portal now.

---

Create a README.md that explains this directory. (prompts.md will help with this.)
Mention how to update the data and any other setup / maintenance activities.

---

The revised glassdoor.json messes up index.html when it loads. Fix this and any subsequent errors.

Uncaught TypeError: Cannot read properties of undefined (reading 'description')
    at viewOverview (gramener-glassdoor/:731:42)
    at gramener-glassdoor/:1194:21
    at Array.forEach (<anonymous>)
    at render (gramener-glassdoor/:1190:9)
    at gramener-glassdoor/:1295:1

<!-- codex resume 01a0c491-0dc9-7730-a57c-009a96b22abf --yolo -->

## Update datastories page, 09 Aug 2026

<!-- Created at ~/Documents/data/glassdoor/ and then moved to ~/code/datastories/gramener-glassdoor/ -->

<!--
cd ~/code/datastories/
dev.sh -p ~/code/scripts:ro -- claude --model opus --effort medium
-->

Update config.json to include gramener-glassdoor/
Generate a screenshot, compressing it as much as possible into .avif or .webp. See ~/code/scripts/setup.fish for my preferred settings.

<!-- claude --resume 5e054e1d-22d3-4090-aadf-d9015a6779c0 -->

## Create a home page, 09 Aug 2026

<!--
cd ~/Documents/data/glassdoor
dev.sh -- claude --dangerously-skip-permissions --model opus --effort medium
-->

Create an `index.html` that `fetch()` from glassdoor.json and renders Gramener Glassdoor data.

The aim is for the users to be able to navigate the information, read reviews and details, and get a good sense of the company.

Think about

- how they'd want to navigate (sort, search, filter, etc.)
- what aggregated information would be useful to show (e.g. ratings, pros/cons, timelines / frequencies, etc.)
- how to present the information in an intuitive way

... and render this page.

---

A few revisions:

- If I update glassdoor.json, will all content be auto-updated? If not, make it so.
- Add an option to expand / collapse all FAQs.
- FAQ: "What is the interview process like at Gramener?" reports "KEY NOT SPECIFIED". Fix that. Find and fix similar issues.
- The text contrast of the FAQ answers is too low. Fix that. Find and fix similar issues.
- Keeping the .review cards to half the container width means that the Pros and Cons are too narrow for long text. Fix that. Find and fix similar issues.
- In the individual reviews, I couldn't find tags CEO Approval, Recommend, Business Outlook, etc. Fix that and allow filtering by those. Find and fix similar issues.

<!-- claude --resume 50a7a7e2-45e8-4f3a-bf64-6e08a320cb64 --dangerously-skip-permissions -->

## Scrape Gramener Glassdoor Reviews, 05 Aug 2026

<!--
cd ~/Documents/data/glassdoor
dev.sh -- codex --yolo --model gpt-5.6-sol --config model_reasoning_effort=medium
-->

Extract all Gramener-related information from Glassdoor into `glassdoor.json` from:

- Overview: https://www.glassdoor.co.in/Overview/Working-at-Gramener-EI_IE942627.11,19.htm
- Reviews: https://www.glassdoor.co.in/Reviews/Gramener-Reviews-E942627.htm
  - Merge with Reviews (employer view): https://www.glassdoor.co.in/employers/ec/reviews/employeeReviews.htm?currentPartnerId=205714&selectedEmployerId=942627&profileId=1118979
- Pay and benefits: https://www.glassdoor.co.in/pay-and-benefits/Gramener-E942627
- Job interviews: https://www.glassdoor.co.in/Interview/Gramener-Interview-Questions-E942627.htm
  - Merge with Interview reviews: https://www.glassdoor.co.in/employers/ec/reviews/interviewReviews.htm?currentPartnerId=205714&selectedEmployerId=942627&profileId=1118979

Extract all information. For example, for ratings that might mean:

- Summary: Overall rating, rating by parameter, % of recommend, % of CEO approval, % of business outlook
- Individual reviews
  - URL
  - Rating
  - Breakdown of ratings (Work-Life Balance, Culture & Values, Career Opportunities, Compensation & Benefits, Senior Management)
  - Date
  - Title
  - Role
  - How long they worked
  - Location
  - Responses for Recommend, CEO Approval, Business Outlook
  - Pros, Cons, Advice to Management (you may need to click on show more if required)
  - Employer response if any
  - Helpful count if any
  - Any other fields

Apply the same principles for other sections.
Since the aim is to extract all useful information and I may have missed some, a useful strategy is to visit all pages (fetching it on the browser and then extracting the DOM) and saving it to a cache file, and then analyzing it offline to extract all information.

Use CDP on localhost:9222 for scraping - I'm logged in.

<!-- codex resume 019fcf7c-74dc-76f3-96ac-64e5cea46630 --yolo -->
