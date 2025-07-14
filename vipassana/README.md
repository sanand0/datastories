# Vipassana

## I attended a 10-day Vipassana meditation center.

![](./i-attended-a-10-day-vipassana-meditation-center.webp)

## Each day had 12 hours of meditation, ...

![](./each-day-had-12-hours-of-meditation.webp)

## 7 hours sleep...

![](./7-hours-sleep.webp)

## 3 hours rest...

![](./3-hours-rest.webp)

## ... and 2 hours to eat.

![](./and-2-hours-to-eat.webp)

## You live like a monk. It's a hostel life.

![](./you-live-like-a-monk-it-s-a-hostel-life.webp)

## The food is basic. You wash utensils and your room.

![](./the-food-is-basic-you-wash-utensils-and-your-room.webp)

## There are rules. No phone, laptop, no communication.

![](./there-are-rules-no-phone-laptop-no-communication.webp)

## You can't speak to anyone. As an introvert, I enjoyed this!

![](./you-can-t-speak-to-anyone-as-an-introvert-i-enjoyed-this.webp)

## You can't kill. Sparing cockroaches and mosquitos were hard.

![](./you-can-t-kill-sparing-cockroaches-and-mosquitos-were-hard.webp)

## You can't mix meditations. But I continued daily Yoga.

![](./you-can-t-mix-meditations-but-i-continued-daily-yoga.webp)

## You can't steal. But I did smuggle a peanut chikki out.

![](./you-can-t-steal-but-i-did-smuggle-a-peanut-chikki-out.webp)

## No intoxicants or sexual misconducts.

![](./no-intoxicants-or-sexual-misconducts.webp)

## You're woken up by bell at 4 am daily.

![](./you-re-woken-up-by-bell-at-4-am-daily.webp)

## You sit cross-legged without moving, which I found impossible.

![](./you-sit-cross-legged-without-moving-which-i-found-impossible.webp)

## I was the sole attendee who needed a backrest.

![](./i-was-the-sole-attendee-who-needed-a-backrest.webp)

## I blame back muscle loss which accompanied my weight loss.

![](./i-blame-back-muscle-loss-which-accompanied-my-weight-loss.webp)

## You observe your sensations calmly.

![](./you-observe-your-sensations-calmly.webp)

## Don't imagine sensations. Don't like or hate them.

![](./don-t-imagine-sensations-don-t-like-or-hate-them.webp)

## It's pragmatic. Accept what works. Reject what doesn't.

![](./it-s-pragmatic-accept-what-works-reject-what-doesn-t.webp)

## There's no dogma. More science than religion.

![](./there-s-no-dogma-more-science-than-religion.webp)

## I discovered several cravings and aversions

![](./i-discovered-several-cravings-and-aversions.webp)

## ... like fear of losing money and an efficiency obsession.

![](./like-fear-of-losing-money-and-an-efficiency-obsession.webp)

## Also that humor, curiosity and compassion really help.

![](./also-that-humor-curiosity-and-compassion-really-help.webp)

## It was 10 days well spent. I strongly recommend it.

![](./it-was-10-days-well-spent-i-strongly-recommend-it.webp)

# Process

**STEP 1**: Create [`captions.txt`](captions.txt) which was my storyline. Each caption becomes a panel.

**STEP 2**: Generate [`prompts.txt`](prompts.txt) with prompts for each panel.

```bash
cat captions.txt | llm -m gpt-4.1-mini -s 'Captions are provided one per line.
For each, write an LLM prompt to draw a comic panel for that caption in the context of the story.
This is set in a Vipassana meditation center in Chennai for men. Fully clothed.
Always show the protagonist, wearing a T-shirt. No text or dialogues. Clear visual story.
Respond with caption & prompt, tab-delimited, one per line' | tee prompts.txt
```

**STEP 3**: Generate the images by running [`make_comic.sh`](make_comic.sh).

**STEP 4**: Delete any images I don't like and re-run [`make_comic.sh`](make_comic.sh).
