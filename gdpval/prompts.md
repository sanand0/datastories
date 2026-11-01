# GDPVal

## Add comparison page, 30 Oct 2026

<!-- Refresh GDPval Data: https://chatgpt.com/c/6ae49513-cae4-83ec-a652-cf4517a66156 (2026-11-01T17:34:13+05:30) -->

https://sanand0.github.io/datastories/gdpval/
~/code/data stories/gdpval/ on [LocalMCP2](/plugins/plugin_asdk_app_6ab0b6c561508191882e58b23665db3e) Is there more recent data than what this data story has? And are we able to reliably refresh it? Give it a shot and test it out. No need to commit or push.

Is it possible? I would prefer to retain the earlier view and build a comparison and over time plan to have some kind of time series to show how these have evolved. Therefore, if it is possible to preserve the categories, that would be ideal

---

I don't need a side by side comparison. I prefer a smooth morphing from the 2025 to the 2026 results - both of size and colour. That means that the new tasks will need to be attributes to the professions as best as possible and as close to the original study intent as possible. That's what will make the story compelling.

LocalMCP2 is not available, so make the change in a new branch on [![Image](https://files.openai.com/content?id=file_00000000fb9881f99f77ad57947232ae&cdn=1&cp=pi&ma=31190400&ts=0&p=pi&cid=8&sig=b9da986568361f3300fc047ef19ef27b2e275443189ff9886f609f394642bbde&v=0)Remote Desktop Commander](/plugins/plugin_asdk_app_6a057d268ebc81919918d37eec718425) on Plutonium from scratch and run it on Plutonium as a HTTP server accessible via Tailscale so I can preview it. Don't commit anything yet.

---

I prefer creating just one new page, /change/, which features this new visual, and a link from the original page to this one.

Make the change, commit and push to the feature branch, make sure this branch gets published on GitHub pages.

---

Simplify the language on the comparison page. UK Govt Comms style of simplicity and clarity. Commit and push to the same branch.

---

In the gdpval/ directory, .gitignore and/or delete what's not required any more. Retain gdpval/prompts.md which I created.

Improve the UI. The comparison page has no margin. After morphing, the color scale doesn't look as nice as the D3 RdYlGn scale for some reason.

---

Wider page margins look worse. I prefer the older left/right margins. It would help if the comparison page had margins at the top and bottom though. Commit and push.
