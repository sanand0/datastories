# Security at Bagmane Capital

## Create the story, 11 Jul 2026

<!--
cd /home/sanand/code/datastories/security-at-bagmane-capital
dev.sh -- claude --dangerously-skip-permissions --model fable --effort medium
-->
<!-- Source: https://chatgpt.com/c/6a520c51-2e08-83e8-8073-a1b703bdd45c -->

Create a polished, responsive scrollytelling webpage from the story below.

Build it as a single self-contained `index.html` that runs directly and on GitHub Pages. Use MapLibre GL JS with a free OpenFreeMap basemap. Inline all story data, CSS, JavaScript, icons and converted route geometry; only the map tiles and MapLibre library may load externally.

Inspect the `.kml` files in this directory and use their actual routes. Match routes to the corresponding moments in the story. Use the supplied coordinates for all other locations. Do not call routing, geocoding or other APIs.

Design this as an entertaining visual narrative, not merely text beside a map:

- Keep a full-screen map fixed while concise story cards advance on scroll.
- Break the story into well-paced scenes, preserving its dry, escalating humour.
- For every scene, animate to the relevant point or fit the relevant route.
- Add, remove or replace routes and placemarks as the narrative changes.
- Clearly contrast the expected 2 km route with the absurd 4 km detour.
- Animate travel direction along routes where useful.
- Make time pressure visible through restrained clocks, timestamps, distance and ETA annotations.
- Build tension toward the late arrival, then treat the security confrontation with deadpan repetition.
- End quietly and anticlimactically at Bug & Bean with the peri peri paneer sandwich.
- Use elegant typography, a restrained Bengaluru-inspired palette, subtle motion and excellent visual hierarchy. Avoid generic dashboard styling, excessive UI, gradients and decorative clutter.

Each scene must declaratively specify its complete visible map state so scrolling backward works correctly. Use `fitBounds` for routes and suitable responsive padding so the story card never obscures the important geography.

Include:

- desktop and mobile layouts
- forward and backward scroll transitions
- keyboard navigation and a small progress indicator
- clickable location names linking to the URLs in the story
- tooltips or labels for important places
- reduced-motion support
- graceful errors if a KML file cannot be parsed
- no frameworks, build step or server requirement

You may lightly edit and divide the prose for rhythm and clarity, but preserve every factual event, the first-person voice and the understated humour. Choose a strong title and opening hook.

After implementation, open and test the page, fix JavaScript and layout problems, and ensure every route and scene appears in the correct narrative order.

**STORY:**

I was staying at [The Curzon Court, Brigade Road](https://maps.app.goo.gl/ArHn75eAihHzZXcr9). 12.97454856819103, 77.60788450296555

I needed to be at [Microsoft Luxor North Tower](https://maps.app.goo.gl/Tf5qZGwXogetSJr46) 12.984402817080221, 77.70407412470264 for a 2 pm [workshop](https://hasgeek.com/fifthelephant/when-data-is-for-agents-workshop/).

So I came over to [Seetharampalya Metro Station](https://maps.app.goo.gl/Z4deFUzZsqamcCZC9) 12.98116461318051, 77.70872373073122
and seated myself at [Fairfield by Marriott](https://maps.app.goo.gl/NJqUfFnHL4QW8xa2A) 12.981961760138114, 77.70869689674738
by 11 am.

At around 1:10 pm, I thought it best to head to the venue. It was a 14 minute walk. That would give me half an hour to have lunch. I skipped breakfast, too.

Unfortunately, the security guard at [Bagmane Capital](https://www.bagmanegroup.com/portfolio/bagmane-capital) Gate 3 12.98465457451843, 77.70619827684402 told me that this was the back gate.

Visitors must register at the front gate near [Sri Vishnu Palace](https://maps.app.goo.gl/i5fWhTzwuaXnnGPd8) 12.97960581201111, 77.69515637422329.

That's 2 km away. But since I can't go through the campus, it's 4 km away.

I called the host and let them know I'll be late.

After ordering a Rapido bike, hunting gate after gate for the right one, I managed to get to the Bagmane Capital front gate 12.9800989885602, 77.69530463499706 at 1:50 pm.

The bus would arrive at 2 pm. The workshop was at 2 pm. It was a 24 minute walk. Since I brisk-walk 25% faster than Google Maps, I could be there by 2:10 pm by walk. Bus was uncertain.

So I brisk-walked.

And ended up in my own workshop 15 minutes late.

Without breakfast. Or lunch.

After the workshop, I walked out via the Gate 3 12.98465457451843, 77.70619827684402. The security turned me around.

I turned around. But after 5 minutes, I turned back.

I took off my visitor badge and walked out.

He shouted at me to turn around. I kept walking.

He followed me, shouting. I kept walking, tiredly.

He called the security at the next check, who stood in front of me, blocking me, and asked what I thought I was doing.

"I'm just going out," I said, tiredly. And walked around him.

He followed me, shouting. I kept walking, tiredly.

I had lunch at [Bug & Bean Cafe](https://maps.app.goo.gl/cCirwrPvdXRVUBnK9) 12.98598655535808, 77.70782368623773.

Unfortunately, their chef was unavailable, so most of the interested dishes were unavailable too. I had a peri peri paneer sandwich.

--- <!-- steering -->

Make this a mobile-friendly story.

At any step, try and zoom as much as is reasonable so that only the relevant points / routes are covered, not too much more - and that the points and step cards are both visible - one does not obscure the other.

After the workshop, the first security guard stopped me from exiting at 12.984721933305083, 77.70473237829793 - the second security guard stopped me at the Gate 3 location.

<!-- claude --resume 25aeaeea-79e2-4025-afcf-9dbf5ecba383 --dangerously-skip-permissions -->
