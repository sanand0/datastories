## User

This article is about how AI is transforming work at Anthropic. Suggest how the following engineer productivity patterns can be illustrated using interactive animated charts, graphs, or infographics.

Specifically show the before-vs-after impact of AI on these engineer productivity patterns:

1. Engineers are getting a lot more done, becoming more "full-stack" (able to succeed at tasks beyond their normal expertise)
2. Engineers are accelerating their learning and iteration speed (tighter feedback loops)
3. Engineers are tackling previously-neglected tasks.

For each pattern, I want 3 different animated graphs.

- Define metrics before coding. Pick what will best illustrate the pattern. Generate REALISTIC synthetic data when required, grounded in the article.
- Be diverse. Xenographics are welcome. Novel animation / interaction styles, artistry, xenographics, and diverse chart types are encouraged.
- Be intuitive. A single glance should tell them exactly what insight we are trying to convey.
- Ensure animation. It should be smooth, engaging, and visually appealing. Interactivity is a plus.

Render this as a single HTML file with tabs for each productivity pattern, and a gallery of animated charts for each pattern.

Here is the article:

---

# How AI is transforming work at Anthropic

Dec 3, 2025

How is AI changing the way we work? Our [previous research](https://www.anthropic.com/economic-index) on AI’s economic impacts looked at the labor market as a whole, covering a variety of different jobs. But what if we studied some of the earliest adopters of AI technology in more detail—namely, us?

Turning the lens inward, in August 2025 we surveyed 132 Anthropic engineers and researchers, conducted 53 in-depth qualitative interviews, and studied internal [Claude Code](https://www.anthropic.com/claude-code) usage data to find out how AI use is changing things at Anthropic. We find that AI use is radically changing the nature of work for software developers, generating both hope and concern.

Our research reveals a workplace facing significant transformations: Engineers are getting a lot more done, becoming more “full-stack” (able to succeed at tasks beyond their normal expertise), accelerating their learning and iteration speed, and tackling previously-neglected tasks. This expansion in breadth also has people wondering about the trade-offs—some worry that this could mean losing deeper technical competence, or becoming less able to effectively supervise Claude’s outputs, while others embrace the opportunity to think more expansively and at a higher level. Some found that more AI collaboration meant they collaborated less with colleagues; some wondered if they might eventually automate themselves out of a job.

We recognize that studying AI’s impact at a company building AI means representing a privileged position—our engineers have early access to cutting-edge tools, work in a relatively stable field, and are themselves contributing to the AI transformation affecting other industries. Despite this, we felt it was on balance useful to research and publish these findings, because what’s happening inside Anthropic for engineers may still be an instructive harbinger of broader societal transformation. Our findings imply some challenges and considerations that may warrant early attention across sectors (though see the Limitations section in the [Appendix](https://anthropic.com/research/how-ai-is-transforming-work-at-anthropic#appendix)for caveats). At the time this data was collected, Claude Sonnet 4 and Claude Opus 4 were the most capable models available, and capabilities have continued to advance.

More capable AI brings productivity benefits, but it also raises questions about maintaining technical expertise, preserving meaningful collaboration, and preparing for an uncertain future that may require new approaches to learning, mentorship, and career development in an AI-augmented workplace. We discuss some initial steps we’re taking to explore these questions internally in the Looking Forward section below. We also explored potential policy responses in our recent blog post on [ideas for AI-related economic policy](https://www.anthropic.com/research/economic-policy-responses).

## Key findings

In this section, we briefly summarize the findings from our survey, interviews, and Claude Code data. We provide detailed findings, methods, and caveats in the subsequent sections below.

**Survey data**

1. **Anthropic engineers and researchers use Claude most often for fixing code errors and learning about the codebase**. Debugging and code understanding are the most common uses (Figure 1).
2. **People report increasing Claude usage and productivity gains.** Employees self-report using Claude in 60% of their work and achieving a 50% productivity boost, a 2-3x increase from this time last year. This productivity looks like slightly less time per task category, but considerably more output volume (Figure 2).
3. **27% of Claude-assisted work consists of tasks that wouldn't have been done otherwise**, such as scaling projects, making nice-to-have tools (e.g. interactive data dashboards), and exploratory work that wouldn't be cost-effective if done manually.
4. **Most employees use Claude frequently while reporting they can “fully delegate” 0-20% of their work to it.** Claude is a constant collaborator but using it generally involves active supervision and validation, especially in high-stakes work—versus handing off tasks requiring no verification at all.

**Qualitative interviews**

1. **Employees are developing intuitions for AI delegation**. Engineers tend to delegate tasks that are easily verifiable, where they “can relatively easily sniff-check on correctness”, low-stakes (e.g. “throwaway debug or research code”), or boring (“The more excited I am to do the task, the more likely I am to not use Claude”). Many describe a trust progression, starting with simple tasks and gradually delegating more complex work—and while they’re currently keeping most design or “taste” tasks, this boundary is being renegotiated as models improve.
2. **Skillsets are broadening into more areas, but some are getting less practice.** Claude enables people to broaden their skills into more areas (of software engineering (“I can very capably work on front-end, or transactional databases... where previously I would've been scared to touch stuff”), but some employees are also concerned, paradoxically, about the atrophy of deeper skillsets required for both writing and critiquing code—“When producing output is so easy and fast, it gets harder and harder to actually take the time to learn something.”
3. **Changing relationship to coding craft.** Some engineers embrace AI assistance and focus on outcomes (“I thought that I really enjoyed writing code, and I think instead I actually just enjoy what I get out of writing code”); others say that “there are certainly some parts of \[writing code\] that I miss.”
4. **Workplace social dynamics may be changing.** Claude is now the first stop for questions that used to go to colleagues—some report fewer mentorship and collaboration opportunities as a result. (“I like working with people and it's sad that I ‘need’ them less now… More junior people don't come to me with questions as often.”)
5. **Career evolution and uncertainty.** Engineers report shifting toward higher-level work managing AI systems and report significant productivity gains. However, these changes also raise questions about the long-term trajectory of software engineering as a profession. Some express conflicting feelings about the future: “I feel optimistic in the short term but in the long term I think AI will end up doing everything and make me and many others irrelevant.” Others emphasize genuine uncertainty, saying only that it was “hard to say” what their roles might look like in a few years’ time.

**Claude Code usage trends**

1. **Claude is handling increasingly complex tasks more autonomously**. Six months ago, Claude Code would complete about 10 actions on its own before needing human input. Now, it generally handles around 20, needing less frequent human steering to complete more complex workflows (Figure 3). Engineers increasingly use Claude for complex tasks like code design/planning (1% to 10% of usage) and implementing new features (14% to 37%) (Figure 4).
2. **Claude fixes a lot of “papercuts”.** 8.6% of Claude Code tasks involve fixing minor issues that improve quality of life, like refactoring code for maintainability (that is, “fixing papercuts”) that people say would typically be deprioritized. These small fixes could add up to larger productivity and efficiency gains.
3. **Everyone is becoming more “full-stack”.** Different teams use Claude in different ways, often to augment their core expertise—Security uses it to analyze unfamiliar code, Alignment & Safety use it to build front-end visualizations of their data, and so on (Figure 5).

## Survey data

We surveyed 132 Anthropic engineers and researchers from across the organization about their Claude use, to better understand how exactly they were using it day-to-day. We distributed our survey through internal communication channels and direct outreach to employees across diverse teams representing both research and product functions. We have included a Limitations section in the Appendix with more methodological details, and we are sharing [our survey questions](https://assets.anthropic.com/m/6cd21f7d4f82afcb/original/Claude-at-Work-Survey.pdf) so others can evaluate our approach and adapt it for their own research.

### What coding tasks are people using Claude for?

We asked the surveyed engineers and researchers to rate how often they used Claude for various types of coding tasks, such as “debugging” (using Claude to help fix errors in code), “code understanding” (having Claude explain existing code to help the human user understand the codebase), “refactoring” (using Claude to help restructure existing code), and “data science” (e.g. having Claude analyze datasets and make bar charts).

Below are the most common daily tasks. Most employees (55%) used Claude for debugging on a daily basis. 42% used Claude everyday for code understanding, and 37% used Claude everyday for implementing new features. The less-frequent tasks were high level design/planning (likely because these are tasks people tend to keep in human hands), as well as data science and front-end development (likely because they are overall less common tasks). This roughly aligns with the Claude Code usage data distribution reported in the “Claude Code usage trends” section.

![Figure 1: Proportion of daily users (x-axis) for various coding tasks (y-axis).](https://www-cdn.anthropic.com/images/4zrzovbb/website/64a18b1756d8954a93e1356f1330ec11075fbe54-3840x2160.png)

_Figure 1: Proportion of daily users (x-axis) for various coding tasks (y-axis)._

###

Usage and productivity

Employees self-reported that 12 months ago, they used Claude in 28% of their daily work and got a +20% productivity boost from it, whereas now, they use Claude in 59% of their work and achieve +50% productivity gains from it on average. (This roughly corroborates the 67% increase in merged pull requests—i.e. successfully incorporated changes to code—per engineer per day we saw when we adopted Claude Code [across our Engineering org](https://newsletter.pragmaticengineer.com/p/how-claude-code-is-built).) The year-on-year comparison is quite dramatic—this suggests a more than 2x increase in both metrics in one year. Usage and productivity are also strongly correlated, and at the extreme end of the distribution, 14% of respondents are increasing their productivity by more than 100% by using Claude—these are our internal “power users.”

To caveat this finding (and other self-reported productivity findings below), productivity is difficult to precisely measure (see [Appendix](https://anthropic.com/research/how-ai-is-transforming-work-at-anthropic#appendix) for more limitations). There is [recent work from METR](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/), an AI research nonprofit, showing that experienced developers working with AI on highly familiar codebases overestimated their productivity boost from AI. That being said, the factors that METR identified as contributing to lower productivity than expected (e.g. AI performing worse in large, complex environments, or where there’s a lot of tacit knowledge/context necessary) closely correspond to the types of tasks our employees said they _don’t_ delegate to Claude (see [AI delegation approaches](https://anthropic.com/research/how-ai-is-transforming-work-at-anthropic#ai-delegation-approaches), below). Our productivity gains, self-reported _across_ tasks, might reflect employees developing strategic AI delegation skills—something not accounted for in the METR study.

An interesting productivity pattern emerges when asking employees, for task categories where they currently use Claude, how it affects their overall time spent and work output volume in that task category. Across almost all task categories, we see a net decrease in time spent, and a larger net increase in output volume:

![Figure 2: Impact on time spent (left panel) and output volume (right panel) by task (y-axis). The x-axis on each plot corresponds to either a self-reported decrease (negative values), increase (positive values) or no change (vertical dashed line) in time spent or output volume for categories of Claude-assisted tasks, compared to not using Claude. Error bars show 95% confidence intervals. Circle area is proportional to the number of responses at each rating point. Only respondents who reported using Claude for each task category are included.](https://www-cdn.anthropic.com/images/4zrzovbb/website/9449bf9393743105a414e17324f30970208ce14b-3840x2160.png)

_Figure 2: Impact on time spent (left panel) and output volume (right panel) by task (y-axis). The x-axis on each plot corresponds to either a self-reported decrease (negative values), increase (positive values) or no change (vertical dashed line) in time spent or output volume for categories of Claude-assisted tasks, compared to not using Claude. Error bars show 95% confidence intervals. Circle area is proportional to the number of responses at each rating point. Only respondents who reported using Claude for each task category are included._

However, when we dig deeper into the raw data, we see that the time saving responses cluster at opposite ends—some people spend significantly _more_ time on tasks that are Claude-assisted.

Why is that? People generally explained that they had to do more debugging and cleanup of Claude’s code (e.g. “when I vibe code myself into a corner”), and shoulder more cognitive overhead for understanding Claude’s code since they didn’t write it themselves. Some mentioned spending more time on tasks in an enabling sense—one said that using Claude helps them “persist on tasks that I previously would've given up on immediately”; another said it helps them do more thorough testing and also more learning and exploration in new codebases. It seems that generally, engineers experiencing time savings may be those who are scoping quickly-verifiable tasks for Claude, while those spending more time might be debugging AI-generated code or working in domains where Claude needs more guidance.

It is also not clear from our data where reported time savings are being reinvested—whether into additional engineering tasks, non-engineering tasks, interacting with Claude or reviewing its output, or activities outside of work. Our task categorization framework does not capture all the ways engineers might allocate their time. Additionally, the time savings may reflect perception biases in self-reporting. Further research is needed to disentangle these effects.

Output volume increases are more straightforward and substantial; there is a larger net increase across all task categories. This pattern makes sense when we consider that people are reporting on task categories (like “debugging” overall) rather than individual tasks—i.e. people can spend slightly less time on debugging as a category while producing much more debugging output overall. Productivity is very hard to measure directly, but this self-reported data suggests that AI enables increased productivity at Anthropic primarily through greater output volume.

###

Claude enabling new work

One thing we were curious about: Is Claude enabling qualitatively new kinds of work, or would Claude-assisted work have been done by employees eventually (albeit potentially at a slower rate)?

Employees estimated that 27% of their Claude-assisted work wouldn't have been done without it. Engineers cited using AI for scaling projects, nice-to-haves (e.g. interactive data dashboards), useful but tedious work like documentation and testing, and exploratory work that wouldn't be cost-effective manually. As one person explained, they can now fix more “papercuts” that previously damaged quality of life, such as refactoring badly-structured code, or building “small tools that help accomplish another task faster.” We looked for this in our usage data analysis as well, and [found that](https://anthropic.com/research/how-ai-is-transforming-work-at-anthropic#fixing-papercuts) 8.6% of Claude Code tasks involve ‘papercut fixes.’

Another researcher explained that they ran many versions of Claude simultaneously, all exploring different approaches to a problem:

> People tend to think about super capable models as a single instance, like getting a faster car. But having a million horses… allows you to test a bunch of different ideas… It’s exciting and more creative when you have that extra breadth to explore.

As we'll see in the following sections, this new work often involves engineers tackling tasks outside their core expertise.

### How much work can be fully delegated to Claude?

Although engineers use Claude frequently, more than half said they can “fully delegate” only between 0-20% of their work to Claude. (It’s worth noting that there is variation in how respondents might interpret “fully delegate”—from tasks needing no verification at all to those that are reliable enough to require only light oversight.) When explaining why, engineers described working actively and iteratively with Claude, and validating its outputs—particularly for complex tasks or high-stakes areas where code quality standards are critical. This suggests that engineers tend to collaborate closely with Claude and check its work rather than handing off tasks without verification, and that they set a high bar for what counts as “fully delegated.”

## Qualitative interviews

While these survey findings reveal significant productivity gains and changing work patterns, they raise questions about how engineers are actually experiencing these changes day-to-day. To understand the human dimension behind these metrics, we conducted in-depth interviews with 53 of the Anthropic engineers and researchers who responded to the survey, to get more insight into how they’re thinking and feeling about these changes in the workplace.

### AI delegation approaches

Engineers and researchers are developing a variety of strategies for productively leveraging Claude in their workflow. People generally delegate tasks that are:

| **Outside the user’s context _and_ low complexity**:“I use Claude for things where I have low context, but think that the overall complexity is also low.”“The majority of the infra\[structure\] problems I have are not difficult and can be handled by Claude… I don’t know Git or Linux very well… Claude does a good job covering for my lack of experience in these areas.”                                                                                                                  |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Easily verifiable:**“It's absolutely _amazing_ for everything where validation effort isn't large in comparison to creation effort.”                                                                                                                                                                                                                                                                                                                                                             |
| **Well-defined or self-contained:**“If a subcomponent of the project is sufficiently decoupled from the rest, I'll get Claude to take a stab.”                                                                                                                                                                                                                                                                                                                                                     |
| **Code quality isn’t critical:**“If it's throwaway debug\[ging\] or research code, it goes straight to Claude. If it's conceptually difficult or needs some very specific type of debug injection, or a design problem, I do it myself.”                                                                                                                                                                                                                                                           |
| **Repetitive or boring:**“The more excited I am to do the task, the more likely I am to not use Claude. Whereas if I'm feeling a lot of resistance… I often find it easier to start a conversation with Claude about the task.”In our survey, on average people said that 44% of Claude-assisted work consisted of tasks they wouldn't have enjoyed doing themselves.                                                                                                                              |
| **Faster to prompt than execute:**“\[For\] a task that I anticipate will take me less than 10 minutes... I'm probably not going to bother using Claude.”“The cold start problem is probably the biggest blocker right now. And by cold start, I mean there is a lot of intrinsic information that I just have about how my team's code base works that Claude will not have by default… I could spend time trying to iterate on the perfect prompt \[but\] I’m just going to go and do it myself.” |

These factors mentioned by our employees in their decisions about delegation were similar to those found to explain AI-related productivity slowdowns (such as high developer familiarity with codebase, large and complex repositories) in an [external study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) from METR. The convergence on these delegation criteria across our interviews suggests that appropriate task choice is an important factor in AI productivity gains (which should be carefully controlled for in future productivity studies).

#### Trust but verify

Many users described a progression in their Claude usage that involved delegating increasingly complex tasks over time: “At first I used AI tools with basic questions about Rust programming language... Lately, I've been using Claude Code for all my coding.”

One engineer likened the trust progression to adopting other technologies, like Google Maps:

> In the beginning I would use \[Google Maps\] only for routes I didn't know... This is like me using Claude to write SQL that I didn't know, but not asking it to write Python that I did. Then I started using Google Maps on routes that I mostly knew, but maybe I didn't know the last mile... Today I use Google Maps all the time, even for my daily commute. If it says to take a different way I do, and just trust that it considered all options... I use Claude Code in a similar way today.

Engineers are split on whether to use Claude within or outside their expertise. Some use it for “peripheral” domains to save implementation time; others prefer familiar territory where they can verify outputs (“I use Claude in such a way where I still have full understanding of what it’s doing”). A security engineer highlighted the importance of experience when Claude proposed a solution that was “really smart in the dangerous way, the kind of thing a very talented junior engineer might propose”. That is, it was something that could only be recognised as problematic by users with judgment and experience.

Other engineers use Claude for both types of tasks, either in an experimental way (“I basically always use Claude to take a first crack at any coding problem”), or by adapting their approach depending on their level of expertise in the task:

> I use the tools for both things that are core to my expertise (as an accelerant, where I know what to expect and can guide the agent effectively), and for things that are slightly outside my area of expertise, where I know roughly what to expect but that Claude is able to fill in the gaps in my memory or familiarity with specific definitions.

> If it's something that I am particularly versed about, I will be more assertive and tell Claude what it needs to track down. If it's something I'm not sure about I often ask it to be the expert and give me options and insights on things I should consider and research.

#### What tasks do people keep for themselves?

People consistently said they didn’t use Claude for tasks involving high-level or strategic thinking, or for design decisions that require organizational context or “taste.” One engineer explained: “I usually keep the high-level thinking and design. I delegate anything I can from new feature development to debugging.” This is reflected in our survey data, which showed the least productivity gains for design and planning tasks (Figure 2). Many people described delegation boundaries as a “moving target,” though, regularly renegotiated as models improve (below, the Claude Code usage data shows relatively more coding design/planning usage now than six months ago).

### Skill transformations

#### New capabilities…

The survey finding that 27% of Claude-assisted work wouldn't have been done otherwise reflects a broader pattern: engineers using AI to work outside their core expertise. Many employees report completing work previously outside their expertise—backend engineers building UIs; researchers creating visualizations. One backend engineer described building a complex UI by iterating with Claude: “It did a way better job than I ever would’ve. I would not have been able to do it, definitely not on time... \[The designers\] were like ‘wait, you did this?’ I said “No, Claude did this - I just prompted it.’”

Engineers report “becoming more full-stack… I can very capably work on front-end, or transactional databases, or API code, where previously I would've been scared to touch stuff I'm less of an expert on.” This capability expansion enables tighter feedback loops and faster learning—one engineer said that a “couple week process” of building, scheduling meetings, and iterating could become “a couple hour working session” with colleagues present for live feedback.

In general, people were enthused by their new ability to prototype quickly, parallelize work, reduce toil, and generally raise their level of ambition. One senior engineer told us, “The tools are definitely making junior engineers more productive and more bold with the types of projects they will take on.” Some also said that the reduced “activation energy” of using Claude enabled them to defeat procrastination more easily, “dramatically decreas\[ing\] the energy required for me to want to start tackling a problem and therefore I'm willing to tackle so many additional things.”

#### …and less hands-on practice

At the same time, some were worried about “skills atrophying as \[they\] delegate more”, and losing the incidental (or “collateral”) learning that happens during manual problem-solving:

> If you were to go out and debug a hard issue yourself, you're going to spend time reading docs and code that isn't directly useful for solving your problem—but this entire time you're building a model of how the system works. There's a lot less of that going on because Claude can just get you to the problem right away.

> I used to explore every config to understand what the tool can do but now I rely on AI to tell me how to use new tools and so I lack the expertise. In conversations with other teammates I can instantly recall things vs now I have to ask AI.

> Using Claude has the potential to skip the part where I learn how to perform a task by solving an easy instance, and then struggle to solve a more complicated instance later.

One senior engineer said they’d be more worried about their skills if they were more junior:

> I’m primarily using AI in cases where I know what the answer should be or should look like. I developed that ability by doing SWE ‘the hard way’... But if I were \[earlier in my career\], I would think it would take a lot of deliberate effort to continue growing my own abilities rather than blindly accepting the model output.

One reason that the atrophy of coding skills is concerning is the “paradox of supervision”—as mentioned above, effectively using Claude requires supervision, and supervising Claude requires the very coding skills that may atrophy from AI overuse. One person said:

> Honestly, I worry much more about the oversight and supervision problem than I do about my skill set specifically… having my skills atrophy or fail to develop is primarily gonna be problematic with respect to my ability to safely use AI for the tasks that I care about versus my ability to independently do those tasks.

To combat this, some engineers deliberately practice without AI: "Every once in a while, even if I know that Claude can nail a problem, I will not ask it to. It helps me keep myself sharp.”

####

Will we still need those hands-on coding skills?

Perhaps software engineering is moving to higher levels of abstraction, which it has done in the past. Early programmers worked much closer to the machine—manually managing memory, writing in assembly language, or even toggling physical switches to input instructions. Over time, higher-level, more human-readable languages emerged that automatically handled complex, low-level operations. Perhaps, in particular with the rise of “vibe coding”, we’re now moving to English as a programming language. One of our staff suggested that aspiring engineers “get good at having AIs \[write code\], and focus on learning higher level concepts and patterns.”

A few employees said they felt that this shift empowers them to think at a higher level—“about the end product and the end user” rather than just the code. One person described the current shift by comparing it to previously having to learn linked-lists in computer science—fundamental structures that higher-level programming languages now handle automatically. “I’m very glad I knew how to do that... \[but\] doing those low level operations isn’t particularly important emotionally. I would rather care about what the code allows me to do.” Another engineer made a similar comparison, but noted that abstraction comes at a cost—with the move to higher-level languages, most engineers lost a deep understanding of memory handling.

Continuing to develop skills in an area can lead to better supervision of Claude and more efficient work (“I notice that when it's something I'm familiar with, it's often faster for me to do it”). But engineers are divided on whether this matters. Some remain sanguine:

> I don't worry too much about skill erosion. The AI still makes me think through problems carefully and helps me learn new approaches. If anything, being able to explore and test ideas more quickly has accelerated my learning in some areas.

Another was more pragmatic: “I am for sure atrophying in my skills as a software engineer... But those skills could come back if they ever needed to, and I just don't need them anymore!” One noted they only lost less-important skills like making charts, and “the kind of code that's critical I can still write very well.”

Perhaps most interestingly, one engineer challenged the premise: “The ‘getting rusty’ framing relies on an assumption that coding will someday go back to the way it was pre-Claude 3.5\. And I don't think it will.”

#### The craft and meaning of software engineering

​​Engineers diverge sharply on whether they miss hands-on coding. Some feel genuine loss—“It’s the end of an era for me - I've been programming for 25 years, and feeling competent in that skill set is a core part of my professional satisfaction.” Others worry about not enjoying the new nature of the work: “Spending your day prompting Claude is not very fun or fulfilling. It's much more fun and fulfilling to put on some music and get in the zone and implement something yourself.”

Some directly addressed the trade-off and accepted it: “There are certainly some parts of \[writing code\] that I miss - getting into a zen flow state when refactoring code, but overall I'm so much more productive now that I'll gladly give that up.”

One person said that iterating with Claude has been _more_ fun, because they can be more picky with their feedback than with humans. Others are more interested in outcomes. One engineer said:

> I expected that by this point I would feel scared or bored… however I don't really feel either of those things. Instead I feel quite excited that I can do significantly more. I thought that I really enjoyed writing code, and instead I actually just enjoy what I get out of writing code.

Whether people embrace AI assistance or mourn the loss of hands-on coding seems to depend on what aspects of software engineering they find most meaningful.

### Changing social dynamics in the workplace

One of the more prominent themes was that Claude has become the first stop for questions that once went to colleagues. “I ask way more questions \[now\] in general, but like 80-90% of them go to Claude," one employee noted. This creates a filtering mechanism where Claude handles routine inquiries, leaving colleagues to address more complex, strategic, or context-heavy issues that exceed AI capabilities (“It has reduced my dependence on \[my team\] by 80%, \[but\] the last 20% is crucial and I go and talk to them”). People also “bounce ideas off” Claude, similar to interactions with human collaborators.

About half reported unchanged team collaboration patterns. One engineer said that he was still meeting with people, sharing context, and choosing directions, and that he thought that in the near future there’d still be a lot of collaboration, but “instead of doing your standard focus work, you’ll be talking to a lot of Claudes.”

However, others described experiencing less interaction with colleagues (“I work way more with Claude than with any of my colleagues.”) Some appreciate the reduced social friction (“I don't feel bad about taking my colleague’s time”). Others resist the change (“I actually don't love that the common response is ‘have you asked Claude?’ I really enjoy working with people in person and highly value that”) or miss the older way of working: “I like working with people and it is sad that I ‘need’ them less now.” Several pointed out the impact on traditional mentorship dynamics, because “Claude can provide a lot of coaching to junior staff” instead of senior engineers. One senior engineer said:

> It's been sad that more junior people don't come to me with questions as often, though they definitely get their questions answered more effectively and learn faster.

###

Career uncertainty and adaptation

Many engineers describe their role shifting from writing code to managing AIs. Engineers increasingly see themselves as “manager\[s\] of AI agents”—some already “constantly have at least a few \[Claude\] instances running.” One person estimated their work has shifted “70%+ to being a code reviewer/reviser rather than a net-new code writer” and another saw “taking accountability for the work of 1, 5, or 100 Claudes” as part of their future role.

In the longer term, career uncertainty is widespread. Engineers saw these changes as harbingers of broader industry transformation, and many said that it was “hard to say” what their careers might look like a few years down the line. Some expressed a conflict between short-term optimism and long-term uncertainty. “I feel optimistic in the short term but in the long term I think AI will end up doing everything and make me and many others irrelevant,” one stated. Others put a finer point on it: “It kind of feels like I'm coming to work every day to put myself out of a job.”

Some engineers were more optimistic. One said, “I fear for the junior devs, but I also appreciate that junior devs are maybe the thirstiest for new technology. I feel generally very optimistic about the trajectory of the profession.” They argued that, while there’s a potential risk of inexperienced engineers shipping problematic code, the combination of better AI guardrails, more built-in educational resources, and natural learning from mistakes will help the field adapt over time.

We asked how people envision their future roles and whether they have any adaptation strategies. Some mentioned plans to specialize further (“developing the skill to meaningfully review AI’s work will take longer and require more specialization”), some anticipated focusing on more interpersonal and strategic work in the future (“we will spend more time finding consensus and let the AIs spend more time on the implementation”). One said they use Claude specifically for career development, getting feedback from it on work and leadership skills (“The rate at which I can learn things or even just be effective without fully learning things just completely changed. I almost feel like the ceiling just shattered for me”).

Overall, many acknowledge deep uncertainty: “I have very low confidence in what specific skills I think will be useful in the future.” A team lead said: “Nobody knows what's going to happen… the important thing is to just be really adaptable.”

## Claude Code usage trends

The survey and interview data show that increased Claude usage is helping people work faster and take on new types of work, though this comes with tensions around AI delegation and skill development. Still, self-reported data only tells part of the story. To complement this, we also analyzed actual Claude usage data across Anthropic teams. Because survey respondents reported Claude Code as the majority of their usage, we used our [privacy-preserving analysis tool](https://www.anthropic.com/research/clio) to analyze 200,000 internal transcripts from Claude Code from February and August 2025.

###

Tackling harder problems with less oversight

Claude Code usage has shifted toward more difficult and autonomous coding tasks over the last six months: (Figure 3):

- **Employees are tackling increasingly complex tasks with Claude Code.** We estimated task complexity of each transcript on a 1-5 scale where 1 corresponds to “basic edits” and 5 is “expert-level tasks requiring weeks/months of human expert work”. Task complexity increased from 3.2 to 3.8 on average.To illustrate the difference between the scores: tasks averaging 3.2 included “Troubleshoot Python module import errors” while tasks averaging 3.8 included “Implement and optimize caching systems.”
- **The maximum number of consecutive tool calls Claude Code makes per transcript increased by 116%.** Tool calls correspond to actions Claude takes using external tools like making edits to files or running commands. Claude now chains together 21.2 independent tool calls without need for human intervention versus 9.8 tool calls from six months ago.
- **The number of human turns decreased by 33%.** The average number of human turns decreased from 6.2 to 4.1 per transcript, suggesting that less human input is necessary to accomplish a given task now compared to six months ago.

![Figure 3. Changes in Claude Code usage between August 2025 and February 2025 (x-axes). Average task complexity increased over time (left panel), average maximum consecutive tool calls per transcript increased over time (middle panel), and number of human turns decreased over time (right panel). Error bars show 95% confidence intervals. The data suggest people are increasingly delegating more autonomy to Claude over time.](https://www-cdn.anthropic.com/images/4zrzovbb/website/d23e1b8d8af84b45d5cffcc6f0a029d635508153-3840x2160.png)

_Figure 3\. Changes in Claude Code usage between August 2025 and February 2025 (x-axes). Average task complexity increased over time (left panel), average maximum consecutive tool calls per transcript increased over time (middle panel), and number of human turns decreased over time (right panel). Error bars show 95% confidence intervals. The data suggest people are increasingly delegating more autonomy to Claude over time._

These usage data corroborate the survey data: engineers delegate increasingly complex work to Claude and Claude requires less oversight. It seems plausible that this is driving the observed productivity gains.

### Distribution of tasks

We classified Claude Code transcripts into one or more types of coding tasks, studying how the uses for different tasks have evolved over the last six months:

![Figure 4. Distribution of various coding tasks (y-axis) as a percentage of the overall number of records (x-axis). We compare the distribution 6 months ago (pink) to present day (purple). The y-axis is ordered by frequency in Feb 2025.](https://www-cdn.anthropic.com/images/4zrzovbb/website/7da627df8a6be4cb90ecd6e6e41345b8122401ed-3840x2160.png)

_Figure 4\. Distribution of various coding tasks (y-axis) as a percentage of the overall number of records (x-axis). We compare the distribution 6 months ago (pink) to present day (purple). The y-axis is ordered by frequency in Feb 2025._

The overall task frequency distribution estimated from usage data roughly aligns with the self-reported task frequency distribution. The most striking change between February and August 2025 is that there now are proportionately many more transcripts using Claude to implement new features (14.3% → 36.9%) and do code design or planning (1.0% → 9.9%). This shift in the relative distribution of Claude Code tasks may suggest that Claude has become better at these more complex tasks, though it could also reflect changes in how teams adopt Claude Code for different workflows rather than increases in absolute work volume (see Appendix for more limitations).

#### Fixing papercuts

We found from the survey that engineers now spend more time making small quality-of-life improvements; in line with this, 8.6% of current Claude Code tasks are classified as “papercut fixes”. These include larger tasks such as creating performance visualization tools and refactoring code for maintainability, as well as smaller tasks like creating terminal shortcuts. This may contribute to engineers’ reported productivity gains (addressing previously neglected quality-of-life improvements may lead to more efficiency over time) and potentially reducing friction and frustration in daily work.

#### Task variation across teams

To study how tasks currently vary across teams, we refined our classification approach to assign each August transcript to a single primary coding task, and split the data by internal teams (y-axis). The stacked bar chart shows the breakdown of coding tasks for each team:

![Figure 5. Each horizontal bar represents a team (y-axis) with segments showing the proportion of that team’s Claude Code usage for different coding tasks (x-axis), color-coded by coding task (legend). Top bar (“All Teams”) represents the overall distribution.](https://www-cdn.anthropic.com/images/4zrzovbb/website/313f1cc36b0eb1fec9ee986f50e8d937ddc796ba-3840x2160.png)

_Figure 5\. Each horizontal bar represents a team (y-axis) with segments showing the proportion of that team’s Claude Code usage for different coding tasks (x-axis), color-coded by coding task (legend). Top bar (“All Teams”) represents the overall distribution._

The "All Teams" bar shows the overall distribution, with the most common tasks being building new features, debugging, and code understanding. This provides a baseline for team-specific comparisons.

Notable team-specific patterns:

1. The **Pre-training** team (who help to train Claude) often uses Claude Code for building new features (54.6%), much of which is running extra experiments.
2. The **Alignment & Safety** and **Post-training** teams do the most front-end development (7.5% and 7.4%) with Claude Code, often for creating data visualizations.
3. The **Security** team often uses Claude Code for code understanding (48.9%), specifically analyzing and understanding the security implications of different parts of the codebase.
4. **Non-technical** employees often use Claude Code for debugging (51.5%), such as troubleshooting network issues or Git operations, as well as for data science (12.7%); Claude appears to be valuable for bridging gaps in technical knowledge.

Many of these team-specific patterns demonstrate the same capability expansion we observed in our survey and interviews: enabling new kinds of work that those on the team either wouldn't have the time or the skillset to do otherwise. For example, the pretraining team ran lots of additional experiments and non-technical employees were able to fix errors in code. And whereas the data suggests that teams do use Claude for their core tasks (for instance, the Infrastructure team most commonly uses Claude Code for infrastructure and DevOps work), Claude often also augments their core tasks (for instance, researchers use Claude for front-end development to better visualize their data). This suggests that Claude is enabling everyone to become more full-stack in their work.

## Looking forward

Anthropic employees have greatly increased their use of Claude over the past year, using it to not only accelerate existing work but to learn new codebases, reduce toil, expand into new domains, and tackle previously neglected improvements. As Claude becomes more autonomous and capable, engineers are discovering new ways to use AI delegation while also figuring out what skills they’ll need in the future. These shifts bring clear productivity and learning benefits alongside genuine uncertainty about the longer-term trajectory of software engineering work. Will AI resemble past software engineering transitions—from lower- to higher-level programming languages, or from individual contributor to manager, as several engineers suggested? Or will it go further?

It’s still early days—Anthropic has many early adopters internally, the landscape is rapidly changing, and our findings likely don’t generalize to other organizations or contexts right now (see Appendix for more limitations). This research reflects that uncertainty: the findings are nuanced, with no single consensus or clear directives emerging. But it does raise questions about how we can thoughtfully and effectively navigate these changes.

To follow up on this initial work, we’re taking several steps. We're talking to Anthropic engineers, researchers, and leadership to address the opportunities and challenges raised. This includes examining how we bring teams together and collaborate with each other, how we support professional development, and/or how we establish best practices for AI-augmented work (e.g. guided by our [AI fluency framework](https://www.anthropic.com/learn/claude-for-you)). We're also expanding this research beyond engineers to understand how AI transformation affects roles across the organization and supporting external organizations such as CodePath as they adapt computer science curricula for an AI-assisted future. Looking ahead, we're also considering structural approaches that may become increasingly relevant as AI capabilities advance, like new pathways for role evolution or reskilling within the organization.

We expect to share more concrete plans in 2026 as our thinking matures. Anthropic is a laboratory for responsible workplace transition; we want to not just study how AI transforms work, but also experiment with how to navigate that transformation thoughtfully, starting with ourselves first.

## Assistant

> **Conceptualizing Interactive Visuals**
>
> I'm now zeroing in on the core interactive aspects. Thinking about the user's need for interactive and animated visuals, I'm sketching out preliminary ideas for incorporating user input to drive the animations and highlight specific data points. The focus now is on translating the three specific data sets to chartable visual forms, suitable for interactive manipulations and transitions.
>
> **Refining Charting Strategies**
>
> I've been analyzing the Anthropic article in depth, extracting key metrics and themes for each engineer productivity pattern. Now I'm focused on transforming these findings into chart-ready data, developing synthetic but realistic datasets for 9 charts. The goal is to build a single HTML file with tabs, incorporating diverse visual styles and smooth animations to illustrate the data patterns.
>
> **Visualizing Engineer Patterns**
>
> I'm translating the engineer productivity patterns from the Anthropic paper into visualizations, focusing on three distinct areas. For the "Full-Stack Expansion" pattern, I'm leaning toward a Skill Web radar chart comparing traditional and AI-augmented engineers' proficiency. I'm also considering radar charts to compare metrics like Time-to-Deploy across these patterns, aiming for clear comparisons. The goal is to highlight key differences with insightful chart-ready datasets.
>
> **Envisioning Interactive Elements**
>
> I'm now concretizing the interactive elements for the second pattern, focusing on animation. Specifically, I'm fleshing out how the circular bar chart can shrink and spin faster to visualize the shortening duration of the feedback loop. Additionally, I'm brainstorming how the animation can bring to life the relationship between AI actions and human interventions. My intention is to create an engaging visual narrative through these interactive and animated components.
>
> **Defining Animations Precisely**
>
> I'm now detailing the specific animations for each chart. For the "Velocity Speedometer," I envision the needle pegging at the max and changing color, emphasizing the increased pull requests. In the "Iceberg Reveal," the "Nice-to-Have" section will emerge visibly. Finally, the "Papercut" chart will see old bug bubbles rapidly disappearing.
>
> **Evaluating Animation Libraries**
>
> I'm now diving into the animation library selection. Initially, I considered using Chart.js, CSS/SVG, and D3, but now I'm leaning heavily towards Chart.js with extensive configuration and custom plugins to maintain consistency and ease of deployment. This approach will allow us to stay in one HTML file. I'm prioritizing diverse chart types and animations within Chart.js.
>
> **Optimizing Visualization Approaches**
>
> I'm shifting focus again, now considering combining Chart.js with custom HTML5 Canvas/SVG visualizations. I'll use Chart.js for data-intensive views and create unique "concept" views using custom visualizations to enhance the "xenographic" aspects and novelty of animations. This revised strategy will give us the best of both worlds, enabling data presentation with creative visual elements. I'm focusing on "Full Stack," "Speed," and "Papercut" visualizations, refining and mixing them to create compelling data narratives.
>
> **Detailing Visual Components**
>
> I'm now detailing each chart's components. For the "Feedback Loop" visualization, I'm developing orbital animations using CSS/SVG, contrasting the before (slow) and after (fast) loop speeds. I'm also planning a scatter chart to represent the shift in Complexity vs. Duration. In the "Neglected Tasks" pattern, I'll use a stacked area chart to show hidden work and a Canvas-based particle system to depict "papercuts" being cleared. Lastly, I'll leverage a treemap or nested boxes to represent resource allocation. To ensure simplicity, I plan to stick with Chart.js for graphs and use CSS animations to add a "Xenographic" feel.
>
> **Designing User Interactions**
>
> Now, I'm integrating user-driven interaction through "Replay Animation" buttons for each chart, ensuring the animated transitions are repeatable. This reinforces the interactive nature and allows for in-depth analysis of the data by the user. I'm focusing on smooth transitions using Chart.js, CSS animations, and JS logic to control chart destruction and recreation. This is to effectively highlight the changes across each animation.
>
> **Generating Final HTML**
>
> I'm now zeroing in on generating the final HTML. I'm focusing on crafting an engaging data narrative with the visualizations. Specifically, I'm working to make the charts effectively tell the story from the prompt. I'm focusing on the implementation and smooth transitions.

Here is a complete, interactive HTML file illustrating the three productivity patterns described in the Anthropic article.

**How to use this:**

1. Save the code below as an `.html` file (e.g., `anthropic_productivity.html`).
2. Open it in any modern web browser.
3. Click the tabs to switch patterns.
4. **Watch the animations:** The charts are programmed to start at the "Before AI" state and dynamically morph into the "After AI" state to visually demonstrate the transformation described in the article. You can hit "Replay Animation" to see the shift again.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anthropic AI Productivity Patterns</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #0f1115; /* Anthropic Dark Theme */
            --card-bg: #1a1d23;
            --text-primary: #e6e6e6;
            --text-secondary: #9ca3af;
            --accent-purple: #a78bfa;
            --accent-cyan: #22d3ee;
            --accent-pink: #f472b6;
            --accent-orange: #fb923c;
        }

        body {
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        h1 {
            font-weight: 300;
            margin-bottom: 10px;
            text-align: center;
        }

        p.subtitle {
            color: var(--text-secondary);
            margin-bottom: 30px;
            text-align: center;
            max-width: 600px;
            line-height: 1.5;
        }

        /* Tabs */
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .tab-btn {
            background-color: var(--card-bg);
            border: 1px solid #333;
            color: var(--text-secondary);
            padding: 12px 24px;
            cursor: pointer;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .tab-btn:hover {
            background-color: #252932;
            color: white;
        }

        .tab-btn.active {
            background-color: #2d2b55;
            color: var(--accent-purple);
            border-color: var(--accent-purple);
            font-weight: 600;
        }

        /* Content Area */
        .content-section {
            display: none;
            width: 100%;
            max-width: 1200px;
            animation: fadeIn 0.5s ease;
        }

        .content-section.active {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Cards */
        .chart-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            border: 1px solid #2a2e36;
        }

        .chart-card h3 {
            margin-top: 0;
            font-size: 1.1rem;
            color: var(--accent-cyan);
            margin-bottom: 5px;
        }

        .chart-card p {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 20px;
            height: 40px; /* Fixed height for alignment */
        }

        .canvas-container {
            position: relative;
            height: 300px;
            width: 100%;
        }

        /* Utility */
        .controls {
            margin-top: 40px;
            text-align: center;
        }

        .replay-btn {
            background: linear-gradient(45deg, var(--accent-purple), var(--accent-pink));
            border: none;
            color: white;
            padding: 10px 30px;
            border-radius: 20px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(167, 139, 250, 0.4);
            transition: transform 0.2s;
        }

        .replay-btn:hover {
            transform: scale(1.05);
        }

        .metric-highlight {
            font-weight: bold;
            color: white;
        }

    </style>
</head>
<body>

    <h1>Anthropic Productivity Patterns</h1>
    <p class="subtitle">Interactive visualization of how AI is transforming engineering work. <br>Charts animate from <strong>"Pre-AI"</strong> to <strong>"AI-Augmented"</strong> states.</p>

    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('pattern1')">1. The "Full-Stack" Expansion</button>
        <button class="tab-btn" onclick="switchTab('pattern2')">2. Speed & Iteration</button>
        <button class="tab-btn" onclick="switchTab('pattern3')">3. Neglected Tasks</button>
    </div>

    <div id="pattern1" class="content-section active">

        <div class="chart-card">
            <h3>The Skill Perimeter</h3>
            <p>Engineers move from narrow specialists to broad generalists. Watch the web expand into Design and Frontend domains.</p>
            <div class="canvas-container">
                <canvas id="chart1_1"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>Cross-Domain Output</h3>
            <p>Volume of work completed outside an engineer's core expertise. AI acts as a bridge for unfamiliar technical territory.</p>
            <div class="canvas-container">
                <canvas id="chart1_2"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>The Output Multiplier</h3>
            <p>Self-reported productivity gains. The shift from manual coding to "Managing Claudes" drives volume up 50%.</p>
            <div class="canvas-container">
                <canvas id="chart1_3"></canvas>
            </div>
        </div>
    </div>

    <div id="pattern2" class="content-section">

        <div class="chart-card">
            <h3>The Autonomy Crossing</h3>
            <p>As Claude chains more tool calls autonomously (purple), the need for human turns (blue) drops, accelerating flow.</p>
            <div class="canvas-container">
                <canvas id="chart2_1"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>Feedback Loop Shrinkage</h3>
            <p>Time required to go from "Idea" to "Verifiable Code". Weeks turn into hours as prototyping accelerates.</p>
            <div class="canvas-container">
                <canvas id="chart2_2"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>Complexity vs. Effort</h3>
            <p>Harder tasks (moving right) now take less time (moving down). The barrier to complex features is lowered.</p>
            <div class="canvas-container">
                <canvas id="chart2_3"></canvas>
            </div>
        </div>
    </div>

    <div id="pattern3" class="content-section">

        <div class="chart-card">
            <h3>The "New Work" Reveal</h3>
            <p>27% of AI-assisted work is net-new. This chart shows "Nice-to-haves" and "Tooling" emerging from zero.</p>
            <div class="canvas-container">
                <canvas id="chart3_1"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>Fixing "Papercuts"</h3>
            <p>Small annoyances (refactoring, shortcuts) were previously ignored. AI allows engineers to clean them up en masse.</p>
            <div class="canvas-container">
                <canvas id="chart3_2"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>The Long Tail of Work</h3>
            <p>High Priority (P0) work remains constant, but the "Long Tail" (P4/P5) of backlog items finally gets addressed.</p>
            <div class="canvas-container">
                <canvas id="chart3_3"></canvas>
            </div>
        </div>
    </div>

    <div class="controls">
        <button class="replay-btn" onclick="replayAnimations()">Replay Transformations</button>
    </div>

    <script>
        // Global Chart Registry
        let charts = {};

        // Shared Configs
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#9ca3af' } },
                tooltip: { backgroundColor: '#1f2937', titleColor: '#fff', bodyColor: '#ccc' }
            },
            scales: {
                y: { grid: { color: '#333' }, ticks: { color: '#777' } },
                x: { grid: { color: '#333' }, ticks: { color: '#777' } }
            }
        };

        // --- DATA & SETUP ---

        function initCharts() {
            Chart.defaults.color = '#9ca3af';
            Chart.defaults.font.family = "'Segoe UI', sans-serif";

            // === PATTERN 1: FULL STACK ===

            // 1.1 Radar: Skill Expansion
            const ctx1_1 = document.getElementById('chart1_1').getContext('2d');
            charts['chart1_1'] = new Chart(ctx1_1, {
                type: 'radar',
                data: {
                    labels: ['Backend', 'Database', 'Frontend', 'UX Design', 'DevOps'],
                    datasets: [{
                        label: 'Before AI',
                        data: [90, 60, 20, 10, 40],
                        borderColor: '#555',
                        backgroundColor: 'rgba(85,85,85,0.2)',
                        borderWidth: 2
                    }, {
                        label: 'With Claude',
                        data: [90, 60, 20, 10, 40], // Starts same, animates out
                        borderColor: '#a78bfa',
                        backgroundColor: 'rgba(167, 139, 250, 0.3)',
                        borderWidth: 2
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: { r: { grid: { color: '#333' }, ticks: { display: false }, suggesteMin: 0, suggestedMax: 100 } }
                }
            });

            // 1.2 Stacked Bar: Cross Domain
            const ctx1_2 = document.getElementById('chart1_2').getContext('2d');
            charts['chart1_2'] = new Chart(ctx1_2, {
                type: 'bar',
                data: {
                    labels: ['Security Team', 'Alignment Team', 'Infra Team'],
                    datasets: [
                        { label: 'Core Tasks', data: [95, 90, 95], backgroundColor: '#4b5563' },
                        { label: 'New Domain (Frontend/Data)', data: [0, 0, 0], backgroundColor: '#22d3ee' } // Starts at 0
                    ]
                },
                options: {
                    ...commonOptions,
                    scales: { x: { stacked: true }, y: { stacked: true, grid: { color: '#333' } } }
                }
            });

            // 1.3 Bar: Productivity
            const ctx1_3 = document.getElementById('chart1_3').getContext('2d');
            charts['chart1_3'] = new Chart(ctx1_3, {
                type: 'bar',
                data: {
                    labels: ['Code Reviewed', 'Features Shipped', 'Bugs Squashed'],
                    datasets: [{
                        label: 'Output Volume',
                        data: [40, 25, 30],
                        backgroundColor: ['#f472b6', '#a78bfa', '#22d3ee'],
                        borderRadius: 5
                    }]
                },
                options: commonOptions
            });

            // === PATTERN 2: SPEED ===

            // 2.1 Line: Autonomy Gap
            const ctx2_1 = document.getElementById('chart2_1').getContext('2d');
            charts['chart2_1'] = new Chart(ctx2_1, {
                type: 'line',
                data: {
                    labels: ['Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6'],
                    datasets: [
                        { label: 'Claude Tool Calls (Autonomy)', data: [10, 10, 10, 10, 10, 10], borderColor: '#a78bfa', tension: 0.4 },
                        { label: 'Human Turns (Oversight)', data: [6.2, 6.2, 6.2, 6.2, 6.2, 6.2], borderColor: '#fb923c', tension: 0.4 }
                    ]
                },
                options: commonOptions
            });

            // 2.2 Horizontal Bar: Loop Speed
            const ctx2_2 = document.getElementById('chart2_2').getContext('2d');
            charts['chart2_2'] = new Chart(ctx2_2, {
                type: 'bar',
                indexAxis: 'y',
                data: {
                    labels: ['Prototyping', 'Refactoring', 'Testing'],
                    datasets: [{
                        label: 'Hours Spent',
                        data: [40, 20, 15],
                        backgroundColor: '#fb923c'
                    }]
                },
                options: commonOptions
            });

            // 2.3 Scatter: Complexity
            const ctx2_3 = document.getElementById('chart2_3').getContext('2d');
            charts['chart2_3'] = new Chart(ctx2_3, {
                type: 'bubble',
                data: {
                    datasets: [{
                        label: 'Task Cluster',
                        data: [
                            { x: 2, y: 10, r: 10 }, // Low complexity, high time
                            { x: 3, y: 12, r: 10 },
                            { x: 1, y: 5, r: 8 }
                        ],
                        backgroundColor: '#22d3ee'
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: {
                        x: { title: { display: true, text: 'Task Complexity (1-5)' }, min: 0, max: 6, grid: { color: '#333' } },
                        y: { title: { display: true, text: 'Hours to Complete' }, min: 0, max: 20, grid: { color: '#333' } }
                    }
                }
            });

            // === PATTERN 3: NEGLECTED TASKS ===

            // 3.1 Stacked Area (Iceberg)
            const ctx3_1 = document.getElementById('chart3_1').getContext('2d');
            charts['chart3_1'] = new Chart(ctx3_1, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [
                        {
                            label: 'Core Work',
                            data: [70, 72, 71, 70, 72, 73],
                            fill: true,
                            backgroundColor: 'rgba(75, 85, 99, 0.5)',
                            borderColor: '#4b5563',
                            tension: 0.3
                        },
                        {
                            label: 'New/Neglected Work',
                            data: [0, 0, 0, 0, 0, 0], // Starts at 0
                            fill: true,
                            backgroundColor: 'rgba(34, 211, 238, 0.5)',
                            borderColor: '#22d3ee',
                            tension: 0.3
                        }
                    ]
                },
                options: { ...commonOptions, scales: { y: { stacked: true }, x: { grid: { color: '#333' } } } }
            });

            // 3.2 Doughnut: Papercuts
            const ctx3_2 = document.getElementById('chart3_2').getContext('2d');
            charts['chart3_2'] = new Chart(ctx3_2, {
                type: 'doughnut',
                data: {
                    labels: ['Critical Features', 'Maintenance', 'Papercut Fixes'],
                    datasets: [{
                        data: [80, 20, 0],
                        backgroundColor: ['#4b5563', '#9ca3af', '#f472b6'],
                        borderWidth: 0
                    }]
                },
                options: { ...commonOptions, plugins: { legend: { position: 'right' } } }
            });

            // 3.3 Bar: Long Tail
            const ctx3_3 = document.getElementById('chart3_3').getContext('2d');
            charts['chart3_3'] = new Chart(ctx3_3, {
                type: 'bar',
                data: {
                    labels: ['P0 (Critical)', 'P1 (High)', 'P2 (Med)', 'P3 (Low)', 'P4 (Nice-to-have)'],
                    datasets: [{
                        label: 'Tasks Completed',
                        data: [50, 40, 20, 5, 2],
                        backgroundColor: ['#fb923c', '#fb923c', '#4b5563', '#4b5563', '#4b5563']
                    }]
                },
                options: commonOptions
            });

            // Trigger initial animation
            setTimeout(() => updateChartsToAfterState(), 500);
        }

        // --- ANIMATION LOGIC ---

        function updateChartsToAfterState() {
            // Pattern 1.1: Radar Expansion
            charts['chart1_1'].data.datasets[1].data = [95, 80, 75, 60, 70]; // Massive expansion in Frontend/Design
            charts['chart1_1'].update();

            // Pattern 1.2: Cross Domain
            charts['chart1_2'].data.datasets[0].data = [60, 60, 70]; // Core work reduces slightly (relative %)
            charts['chart1_2'].data.datasets[1].data = [40, 30, 25]; // New domain work explodes
            charts['chart1_2'].update();

            // Pattern 1.3: Productivity
            charts['chart1_3'].data.datasets[0].data = [80, 55, 65]; // 2x increase
            charts['chart1_3'].update();

            // Pattern 2.1: Autonomy Gap
            charts['chart2_1'].data.datasets[0].data = [10, 12, 15, 18, 20, 21.2]; // AI actions go UP
            charts['chart2_1'].data.datasets[1].data = [6.2, 5.8, 5.5, 5.0, 4.5, 4.1]; // Human turns go DOWN
            charts['chart2_1'].update();

            // Pattern 2.2: Loop Speed
            charts['chart2_2'].data.datasets[0].data = [4, 2, 2]; // Massive reduction in time
            charts['chart2_2'].data.datasets[0].backgroundColor = '#22d3ee'; // Change color to signify optimization
            charts['chart2_2'].update();

            // Pattern 2.3: Scatter shift
            // Move bubbles to right (more complexity) and down (less time)
            charts['chart2_3'].data.datasets[0].data = [
                { x: 3.5, y: 4, r: 12 },
                { x: 4.8, y: 6, r: 15 },
                { x: 2.5, y: 1, r: 8 }
            ];
            charts['chart2_3'].data.datasets[0].backgroundColor = '#a78bfa';
            charts['chart2_3'].update();

            // Pattern 3.1: Iceberg
            charts['chart3_1'].data.datasets[1].data = [5, 10, 15, 20, 25, 27]; // New work appears
            charts['chart3_1'].update();

            // Pattern 3.2: Papercuts
            charts['chart3_2'].data.datasets[0].data = [65, 26.4, 8.6]; // Papercuts emerge
            charts['chart3_2'].update();

            // Pattern 3.3: Long Tail
            charts['chart3_3'].data.datasets[0].data = [52, 45, 40, 35, 30]; // Tail grows significantly
            charts['chart3_3'].data.datasets[0].backgroundColor = ['#fb923c', '#fb923c', '#a78bfa', '#a78bfa', '#a78bfa'];
            charts['chart3_3'].update();
        }

        function resetCharts() {
            // Manually reset data to initial states (simplified for brevity)
            charts['chart1_1'].data.datasets[1].data = [90, 60, 20, 10, 40];
            charts['chart1_2'].data.datasets[1].data = [0, 0, 0];
            charts['chart1_3'].data.datasets[0].data = [40, 25, 30];

            charts['chart2_1'].data.datasets[0].data = [10, 10, 10, 10, 10, 10];
            charts['chart2_1'].data.datasets[1].data = [6.2, 6.2, 6.2, 6.2, 6.2, 6.2];
            charts['chart2_2'].data.datasets[0].data = [40, 20, 15];
            charts['chart2_2'].data.datasets[0].backgroundColor = '#fb923c';
            charts['chart2_3'].data.datasets[0].data = [{x:2,y:10,r:10}, {x:3,y:12,r:10}, {x:1,y:5,r:8}];

            charts['chart3_1'].data.datasets[1].data = [0, 0, 0, 0, 0, 0];
            charts['chart3_2'].data.datasets[0].data = [80, 20, 0];
            charts['chart3_3'].data.datasets[0].data = [50, 40, 20, 5, 2];
            charts['chart3_3'].data.datasets[0].backgroundColor = ['#fb923c', '#fb923c', '#4b5563', '#4b5563', '#4b5563'];

            Object.values(charts).forEach(c => c.update('none')); // Update without animation first
        }

        // --- INTERACTION ---

        function switchTab(tabId) {
            // Hide all
            document.querySelectorAll('.content-section').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

            // Show selected
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');

            // Trigger replay for effect
            replayAnimations();
        }

        function replayAnimations() {
            resetCharts();
            setTimeout(() => {
                updateChartsToAfterState();
            }, 300);
        }

        // Initialize on load
        window.addEventListener('load', initCharts);

    </script>
</body>
</html>
```

## User

Look closely for errors in your output and fix them.

Extend to 3 more animated graphs each.
Be more diverse. Your aim is to give me creative ideas.
Xenographics are welcome. Novel animation / interaction styles, artistry, xenographics, and diverse chart types are encouraged.

## Assistant

> **Considering Project Goals**
>
> I've been meticulously analyzing the initial request. My focus has narrowed to the core components: an interactive HTML file and animated charts. The crucial element is representing the three specific productivity patterns within Anthropic. I'm starting to visualize how to translate these patterns into effective visual narratives.
>
> **Exploring Chart Options**
>
> I've been refining my approach to representing the productivity patterns. I'm focusing on incorporating more visually diverse and unconventional charts, specifically "xenographics". For Pattern 1, I'm leaning toward a Voronoi Treemap or a Force-Directed Graph, moving away from standard stacked bars. The "Before vs. After" animation dynamic is still crucial. I'm aiming for six graphs per pattern to offer a comprehensive visual narrative, fixing any errors from the last iteration.
>
> **Refining Visualization Choices**
>
> I'm now zeroing in on visualization choices for Pattern 2\. A Sankey diagram, looped to illustrate accelerated flows, feels promising. I'm also considering a race track or spiral plot to show the speed of project progress. A particle system for the "Idea -> Shipped" transition offers an abstract, visual representation. Furthermore, a streamgraph might effectively demonstrate the density of commits over time. I'm aiming for visuals that effectively contrast before/after states, as per my previous iterations.
>
> **Analyzing Pattern 3 Ideas**
>
> I'm now focusing on Pattern 3, the "Long Tail," with some fresh visualization concepts. The iceberg metaphor remains solid. But I'm also exploring a beeswarm plot to show neglected tasks becoming active and a pixel grid (mosaic) to represent the "before" and "after" states of papercuts. The "Garden of Code" metaphor, with flowers blooming, offers a compelling artistic approach. I'm aiming to choose the "creative six" visualizations for each pattern. I feel confident about the current direction.
>
> **Expanding Visual Concepts**
>
> I'm now iterating on visualization choices for Pattern 1, the "Inventory of Skills." A zoomable packing diagram seems promising for representing the initial skill set. I'm also considering a network graph to depict the collaboration and tool web dynamics. Additionally, a sunburst chart could effectively illustrate hierarchical skill acquisition. I'm also planning to utilize parallel coordinates for comparing engineer profiles, highlighting the pre- and post-AI impacts on context, speed, and scope.
>
> **Defining Technical Strategy**
>
> I'm now nailing down the technical implementation. I've chosen Chart.js for its simplicity, while pushing its limits with advanced configs and custom canvas drawing. For "xenographic" visualizations, I'm adapting Chart.js to meet the specific visualization needs, as I considered d3.js too cumbersome for this project. My goal is to maximize chart.js capabilities within an interactive HTML file without external build steps. This strategic compromise will streamline the process while still allowing for creative and non-standard visuals.
>
> **Optimizing Code Integration**
>
> I'm now integrating the artistic elements, specifically the network and spiral animations, into the existing Chart.js framework. To maintain reliability and facilitate "Copy-Paste" functionality, I'm opting for HTML5 Canvas API alongside Chart.js. I'm focusing on ensuring smooth animations upon tab switch. I'm also revising color choices to align with the Anthropic palette, and I'm updating to the last visualization of pattern one.
>
> **Crafting Chart Narratives**
>
> I'm now iterating on chart options for the three productivity patterns, exploring more specific implementations. For Pattern 2 ("Speed"), I'm leaning toward a spiral visualization using HTML5 Canvas for its time compression. A Beeswarm plot, also using HTML5 Canvas, will represent the backlog in Pattern 3\. This approach ensures more dynamic and unique visual elements within the project. I'm focusing on writing the code to handle all of the visualizations, including the custom canvas charts and incorporating Chart.js's strengths.

This is a significant expansion. I have corrected the layout issues, optimized the animation logic to prevent memory leaks, and expanded the visualization suite to **6 charts per pattern**.

To achieve true **xenographics** and creative diversity, I have employed a hybrid approach:

1. **Chart.js** for structured, quantitative metrics.
2. **Raw HTML5 Canvas** for custom, physics-based, and artistic visualizations (Beeswarms, Spirals, Network Graphs) that standard libraries cannot easily do.

### How to use

Save as `.html` and open. Use the **"Run AI Transformation"** button to see the global impact.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anthropic AI Work Patterns: Deep Dive</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #151515;
            --card-bg: #1e1e1e;
            --text-main: #ebebeb;
            --text-muted: #888;
            --claude-purple: #D97757; /* Anthropic Accent Tone variant */
            --claude-accent: #d4a27f;
            --chart-red: #ff6b6b;
            --chart-blue: #4dabf7;
            --chart-green: #69db7c;
            --chart-purple: #da77f2;
            --chart-yellow: #fcc419;
            --chart-teal: #20c997;
        }

        body {
            font-family: 'Untitled Sans', 'Segoe UI', system-ui, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 40px;
            overflow-x: hidden;
        }

        h1 {
            font-weight: 400;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            letter-spacing: -0.05em;
        }

        .header-container {
            max-width: 1400px;
            margin: 0 auto 40px auto;
            border-bottom: 1px solid #333;
            padding-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: end;
        }

        .tabs {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            justify-content: center;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.1rem;
            padding: 10px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.3s;
        }

        .tab-btn:hover { color: var(--text-main); }

        .tab-btn.active {
            color: var(--claude-accent);
            border-bottom: 2px solid var(--claude-accent);
        }

        /* Grid Layout */
        .dashboard-grid {
            display: none; /* Hidden by default */
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            max-width: 1600px;
            margin: 0 auto;
            animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .dashboard-grid.active { display: grid; }

        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Card Styling */
        .card {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid #333;
            display: flex;
            flex-direction: column;
            position: relative;
            height: 380px;
            overflow: hidden;
        }

        .card h3 {
            margin: 0 0 10px 0;
            font-size: 1rem;
            font-weight: 500;
            color: var(--claude-accent);
        }

        .card p {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin: 0 0 20px 0;
            line-height: 1.4;
            height: 40px;
        }

        .viz-container {
            flex-grow: 1;
            position: relative;
            width: 100%;
            height: 100%;
        }

        /* Controls */
        .controls {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 100;
            background: rgba(30, 30, 30, 0.9);
            padding: 12px 24px;
            border-radius: 30px;
            border: 1px solid #444;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .magic-btn {
            background: linear-gradient(135deg, #D97757, #C46646);
            border: none;
            color: white;
            padding: 12px 30px;
            border-radius: 20px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(217, 119, 87, 0.3);
            transition: transform 0.2s;
        }

        .magic-btn:hover { transform: scale(1.05); }

        .status-indicator {
            font-size: 0.9rem;
            font-variant-numeric: tabular-nums;
            color: #888;
        }

        /* Specific Canvas Styling */
        canvas { width: 100% !important; height: 100% !important; }

    </style>
</head>
<body>

    <div class="header-container">
        <div>
            <h1>The Anthropic Effect</h1>
            <div style="color: #888;">Visualizing the transformation of engineering work (Before vs. After AI)</div>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('fullstack')">1. The Full-Stack Expansion</button>
        <button class="tab-btn" onclick="switchTab('speed')">2. Velocity & Feedback</button>
        <button class="tab-btn" onclick="switchTab('neglected')">3. The Long Tail</button>
    </div>

    <div id="fullstack" class="dashboard-grid active">
        <div class="card">
            <h3>The Skill Perimeter</h3>
            <p>Engineers traditionally specialize. AI pushes their competence boundary outward into Design and Ops.</p>
            <div class="viz-container"><canvas id="c1_1"></canvas></div>
        </div>
        <div class="card">
            <h3>Knowledge Neural Net</h3>
            <p>Visualizing an engineer's mental model. Isolated clusters connect into a dense mesh.</p>
            <div class="viz-container"><canvas id="c1_2_custom"></canvas></div>
        </div>
        <div class="card">
            <h3>Cross-Pollination</h3>
            <p>Security teams doing Frontend; Research doing Infra. The silos break down.</p>
            <div class="viz-container"><canvas id="c1_3"></canvas></div>
        </div>
        <div class="card">
            <h3>The "Fear" Matrix</h3>
            <p>Tasks plotted by "Unfamiliarity" vs "Action". Previously feared tasks move to "Routine".</p>
            <div class="viz-container"><canvas id="c1_4"></canvas></div>
        </div>
        <div class="card">
            <h3>Language Polyglots</h3>
            <p>Volume of code written in languages the engineer <em>does not</em> know fluently.</p>
            <div class="viz-container"><canvas id="c1_5"></canvas></div>
        </div>
        <div class="card">
            <h3>Tool Orbit</h3>
            <p>The tools an engineer commands. AI acts as gravity, pulling more tools into the engineer's orbit.</p>
            <div class="viz-container"><canvas id="c1_6_custom"></canvas></div>
        </div>
    </div>

    <div id="speed" class="dashboard-grid">
        <div class="card">
            <h3>The Autonomy Index</h3>
            <p>Claude Code tool chains vs. Human Interventions. The "Human-in-the-loop" frequency drops.</p>
            <div class="viz-container"><canvas id="c2_1"></canvas></div>
        </div>
        <div class="card">
            <h3>Time Compression Spiral</h3>
            <p>A project timeline spiraling inward. Long outer loops (Manual) tighten into fast inner loops (AI).</p>
            <div class="viz-container"><canvas id="c2_2_custom"></canvas></div>
        </div>
        <div class="card">
            <h3>Complexity vs. Speed</h3>
            <p>The "Impossible Frontier". High complexity tasks migrate to low-time quadrants.</p>
            <div class="viz-container"><canvas id="c2_3"></canvas></div>
        </div>
        <div class="card">
            <h3>The Waiting Game</h3>
            <p>Breakdown of a task. The grey "Blocked/Researching" bars vanish.</p>
            <div class="viz-container"><canvas id="c2_4"></canvas></div>
        </div>
        <div class="card">
            <h3>Context Switching Cost</h3>
            <p>Mental energy lost to switching. AI keeps context, reducing cognitive load.</p>
            <div class="viz-container"><canvas id="c2_5"></canvas></div>
        </div>
        <div class="card">
            <h3>Throughput Flow</h3>
            <p>Visualizing commits as particles. From a trickle to a steady stream.</p>
            <div class="viz-container"><canvas id="c2_6_custom"></canvas></div>
        </div>
    </div>

    <div id="neglected" class="dashboard-grid">
        <div class="card">
            <h3>The Hidden Iceberg</h3>
            <p>27% of AI work is "Net New"—tasks that simply wouldn't exist without AI efficiency.</p>
            <div class="viz-container"><canvas id="c3_1"></canvas></div>
        </div>
        <div class="card">
            <h3>The Backlog Swarm</h3>
            <p>P4/P5 tasks (grey dots) usually rot. AI activates them (green) and moves them to Done.</p>
            <div class="viz-container"><canvas id="c3_2_custom"></canvas></div>
        </div>
        <div class="card">
            <h3>The "Papercut" Ratio</h3>
            <p>Proportion of time spent on refactoring and quality-of-life fixes.</p>
            <div class="viz-container"><canvas id="c3_3"></canvas></div>
        </div>
        <div class="card">
            <h3>Repo Coverage Heatmap</h3>
            <p>Grid representing codebase files. Dark spots (untouched legacy code) light up.</p>
            <div class="viz-container"><canvas id="c3_4_custom"></canvas></div>
        </div>
        <div class="card">
            <h3>Task Diversity</h3>
            <p>Types of tasks completed. From "Features Only" to a balanced diet of Tests, Docs, and Tools.</p>
            <div class="viz-container"><canvas id="c3_5"></canvas></div>
        </div>
        <div class="card">
            <h3>The "Nice-to-Have" Threshold</h3>
            <p>The cost threshold for building internal tools drops below the value line.</p>
            <div class="viz-container"><canvas id="c3_6"></canvas></div>
        </div>
    </div>

    <div class="controls">
        <span class="status-indicator" id="statusText">State: <strong>Pre-AI Era</strong></span>
        <button class="magic-btn" onclick="toggleAI()">Run AI Transformation</button>
    </div>

<script>
    // --- GLOBAL STATE ---
    let isAI = false;
    let chartInstances = {};
    let animationLoops = []; // Store IDs for custom canvas loops to cancel them

    // Theme Colors
    const C_BG = '#1e1e1e';
    const C_ACCENT = '#d4a27f';
    const C_OLD = '#444';
    const C_NEW = '#D97757';
    const C_NEW_SEC = '#4dabf7';

    // Chart.js Defaults
    Chart.defaults.color = '#888';
    Chart.defaults.borderColor = '#333';
    Chart.defaults.font.family = "'Untitled Sans', system-ui";

    // --- INITIALIZATION ---
    window.onload = function() {
        initCharts();
        initCustomCanvas();
    };

    function switchTab(id) {
        // UI
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        event.target.classList.add('active');

        document.querySelectorAll('.dashboard-grid').forEach(g => g.classList.remove('active'));
        document.getElementById(id).classList.add('active');

        // Restart animations for the visible tab
        stopCustomAnimations();
        initCustomCanvas();
    }

    function toggleAI() {
        isAI = !isAI;
        const btn = document.querySelector('.magic-btn');
        const txt = document.getElementById('statusText');

        if(isAI) {
            btn.innerHTML = "Revert to Manual";
            btn.style.background = "#444";
            txt.innerHTML = "State: <strong>AI Augmented</strong>";
            updateChartsAI();
        } else {
            btn.innerHTML = "Run AI Transformation";
            btn.style.background = "linear-gradient(135deg, #D97757, #C46646)";
            txt.innerHTML = "State: <strong>Pre-AI Era</strong>";
            updateChartsManual();
        }
    }

    // ============================================
    // PART 1: CHART.JS INSTANCES (Standard Charts)
    // ============================================

    function initCharts() {
        // --- PATTERN 1: FULL STACK ---

        // 1.1 Radar
        createChart('c1_1', 'radar', {
            labels: ['Backend', 'DB', 'Frontend', 'Design', 'Ops'],
            datasets: [{ label: 'Skill', data: [90, 70, 20, 10, 30], backgroundColor: 'rgba(212, 162, 127, 0.2)', borderColor: C_ACCENT }]
        });

        // 1.3 Stacked Bar
        createChart('c1_3', 'bar', {
            labels: ['Security', 'Infra', 'Research'],
            datasets: [
                { label: 'Core', data: [100, 100, 100], backgroundColor: '#555' },
                { label: 'New Domain', data: [0, 0, 0], backgroundColor: C_NEW_SEC }
            ]
        }, { scales: { x: { stacked: true }, y: { stacked: true } } });

        // 1.4 Bubble (Fear Matrix)
        createChart('c1_4', 'bubble', {
            datasets: [{
                label: 'Tasks',
                data: [{x: 80, y: 10, r: 10}, {x: 90, y: 5, r: 8}, {x: 20, y: 90, r: 15}], // x: Unfamiliarity, y: Frequency
                backgroundColor: C_OLD
            }]
        }, { scales: { x: { title: {display:true, text:'Unfamiliarity'}}, y: { title: {display:true, text:'Frequency'}} } });

        // 1.5 Polar Area
        createChart('c1_5', 'polarArea', {
            labels: ['Python', 'Go', 'Rust', 'JS/TS', 'SQL'],
            datasets: [{ data: [80, 20, 0, 5, 10], backgroundColor: [C_ACCENT, '#555', '#333', '#333', '#444'] }]
        });


        // --- PATTERN 2: SPEED ---

        // 2.1 Line
        createChart('c2_1', 'line', {
            labels: ['W1', 'W2', 'W3', 'W4'],
            datasets: [
                { label: 'AI Actions', data: [5, 5, 5, 5], borderColor: C_NEW_SEC },
                { label: 'Human Interventions', data: [10, 10, 10, 10], borderColor: C_ACCENT }
            ]
        });

        // 2.3 Scatter
        createChart('c2_3', 'scatter', {
            datasets: [{
                label: 'Features',
                data: [{x: 2, y: 10}, {x: 3, y: 15}, {x: 5, y: 30}], // x: Complexity, y: Time
                backgroundColor: C_OLD
            }]
        });

        // 2.4 Bar (Waterfall style)
        createChart('c2_4', 'bar', {
            labels: ['Research', 'Drafting', 'Debugging', 'Testing'],
            datasets: [{ label: 'Hours', data: [4, 6, 8, 4], backgroundColor: '#666' }]
        });

        // 2.5 Doughnut
        createChart('c2_5', 'doughnut', {
            labels: ['Deep Work', 'Context Switching'],
            datasets: [{ data: [60, 40], backgroundColor: [C_ACCENT, '#333'] }]
        });

        // --- PATTERN 3: NEGLECTED ---

        // 3.1 Stacked Area
        createChart('c3_1', 'line', {
            labels: ['Jan', 'Feb', 'Mar', 'Apr'],
            datasets: [
                { label: 'Core', data: [50, 50, 50, 50], fill: true, borderColor: '#555', backgroundColor: '#55555580' },
                { label: 'New', data: [0, 0, 0, 0], fill: true, borderColor: C_NEW_SEC, backgroundColor: 'rgba(77, 171, 247, 0.5)' }
            ]
        });

        // 3.3 Bar (Horizontal)
        createChart('c3_3', 'bar', {
            labels: ['Refactoring', 'Docs', 'Tooling'],
            datasets: [{ label: 'Hours/Week', data: [1, 0.5, 0], backgroundColor: '#555' }]
        }, { indexAxis: 'y' });

        // 3.5 Rose (Polar)
        createChart('c3_5', 'polarArea', {
            labels: ['Feat', 'Bug', 'Doc', 'Test', 'Tool'],
            datasets: [{ data: [80, 15, 2, 3, 0], backgroundColor: [C_NEW, '#555', '#333', '#333', '#222'] }]
        });

        // 3.6 Bar
        createChart('c3_6', 'bar', {
            labels: ['Dashboard', 'Script', 'Bot'],
            datasets: [
                { label: 'Value', data: [50, 30, 20], backgroundColor: C_NEW },
                { label: 'Cost', data: [80, 40, 60], type: 'line', borderColor: 'white' }
            ]
        });
    }

    function createChart(id, type, data, extraOpts = {}) {
        const ctx = document.getElementById(id).getContext('2d');
        chartInstances[id] = new Chart(ctx, {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: extraOpts.scales || {},
                ...extraOpts
            }
        });
    }

    // ============================================
    // PART 2: DATA UPDATE LOGIC
    // ============================================

    function updateChartsAI() {
        // P1
        chartInstances['c1_1'].data.datasets[0].data = [90, 80, 70, 60, 75]; // Radar Expand
        chartInstances['c1_3'].data.datasets[1].data = [40, 30, 50]; // Stacked Bar
        chartInstances['c1_4'].data.datasets[0].data = [{x: 80, y: 60, r: 12}, {x: 90, y: 50, r: 12}, {x: 20, y: 90, r: 15}]; // Bubble Move
        chartInstances['c1_4'].data.datasets[0].backgroundColor = C_NEW_SEC;
        chartInstances['c1_5'].data.datasets[0].data = [80, 40, 30, 40, 50]; // Polyglot

        // P2
        chartInstances['c2_1'].data.datasets[0].data = [5, 12, 18, 25]; // AI Actions Up
        chartInstances['c2_1'].data.datasets[1].data = [10, 8, 5, 3]; // Human Down
        chartInstances['c2_3'].data.datasets[0].data = [{x: 2, y: 2}, {x: 3, y: 4}, {x: 5, y: 8}]; // Complexity scatter drop
        chartInstances['c2_3'].data.datasets[0].backgroundColor = C_NEW;
        chartInstances['c2_4'].data.datasets[0].data = [1, 2, 3, 2]; // Waterfall shrink
        chartInstances['c2_5'].data.datasets[0].data = [90, 10]; // Doughnut

        // P3
        chartInstances['c3_1'].data.datasets[1].data = [10, 20, 25, 27]; // New work
        chartInstances['c3_3'].data.datasets[0].data = [5, 4, 6]; // Refactoring Up
        chartInstances['c3_3'].data.datasets[0].backgroundColor = C_NEW_SEC;
        chartInstances['c3_5'].data.datasets[0].data = [50, 20, 15, 15, 25]; // Rose Balance
        chartInstances['c3_6'].data.datasets[1].data = [10, 5, 5]; // Cost Crash

        updateAll();
    }

    function updateChartsManual() {
        // Reset Logic (Simplified)
        chartInstances['c1_1'].data.datasets[0].data = [90, 70, 20, 10, 30];
        chartInstances['c1_3'].data.datasets[1].data = [0, 0, 0];
        chartInstances['c1_4'].data.datasets[0].data = [{x: 80, y: 10, r: 10}, {x: 90, y: 5, r: 8}, {x: 20, y: 90, r: 15}];
        chartInstances['c1_4'].data.datasets[0].backgroundColor = C_OLD;
        chartInstances['c1_5'].data.datasets[0].data = [80, 20, 0, 5, 10];

        chartInstances['c2_1'].data.datasets[0].data = [5, 5, 5, 5];
        chartInstances['c2_1'].data.datasets[1].data = [10, 10, 10, 10];
        chartInstances['c2_3'].data.datasets[0].data = [{x: 2, y: 10}, {x: 3, y: 15}, {x: 5, y: 30}];
        chartInstances['c2_3'].data.datasets[0].backgroundColor = C_OLD;
        chartInstances['c2_4'].data.datasets[0].data = [4, 6, 8, 4];
        chartInstances['c2_5'].data.datasets[0].data = [60, 40];

        chartInstances['c3_1'].data.datasets[1].data = [0, 0, 0, 0];
        chartInstances['c3_3'].data.datasets[0].data = [1, 0.5, 0];
        chartInstances['c3_3'].data.datasets[0].backgroundColor = '#555';
        chartInstances['c3_5'].data.datasets[0].data = [80, 15, 2, 3, 0];
        chartInstances['c3_6'].data.datasets[1].data = [80, 40, 60];

        updateAll();
    }

    function updateAll() {
        Object.values(chartInstances).forEach(c => c.update());
    }


    // ============================================
    // PART 3: CUSTOM XENOGRAPHIC ANIMATIONS (Canvas)
    // ============================================

    function initCustomCanvas() {
        // Determine which tab is active and run specific animations
        const activeTab = document.querySelector('.dashboard-grid.active').id;

        if (activeTab === 'fullstack') {
            runNetworkGraph('c1_2_custom');
            runOrbit('c1_6_custom');
        } else if (activeTab === 'speed') {
            runSpiral('c2_2_custom');
            runParticles('c2_6_custom');
        } else if (activeTab === 'neglected') {
            runBeeswarm('c3_2_custom');
            runHeatmap('c3_4_custom');
        }
    }

    function stopCustomAnimations() {
        animationLoops.forEach(id => cancelAnimationFrame(id));
        animationLoops = [];
    }

    // --- 1.2 Network Graph (Nodes connecting) ---
    function runNetworkGraph(canvasId) {
        const canvas = document.getElementById(canvasId);
        if(!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width = canvas.parentElement.offsetWidth;
        const h = canvas.height = canvas.parentElement.offsetHeight;

        let nodes = [];
        for(let i=0; i<30; i++) nodes.push({x: Math.random()*w, y: Math.random()*h, vx: Math.random()-0.5, vy: Math.random()-0.5});

        function draw() {
            ctx.fillStyle = C_BG; ctx.fillRect(0,0,w,h);

            // Interaction: if AI, draw more lines
            const threshold = isAI ? 150 : 60;
            const nodeColor = isAI ? C_NEW_SEC : '#555';

            nodes.forEach(n => {
                n.x += n.vx; n.y += n.vy;
                if(n.x<0 || n.x>w) n.vx*=-1;
                if(n.y<0 || n.y>h) n.vy*=-1;
                ctx.beginPath(); ctx.arc(n.x, n.y, 3, 0, 6.28); ctx.fillStyle = nodeColor; ctx.fill();
            });

            ctx.lineWidth = 1;
            for(let i=0; i<nodes.length; i++){
                for(let j=i+1; j<nodes.length; j++){
                    let d = Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y);
                    if(d < threshold) {
                        ctx.strokeStyle = isAI ? `rgba(77, 171, 247, ${1 - d/threshold})` : `rgba(85, 85, 85, ${1 - d/threshold})`;
                        ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y); ctx.stroke();
                    }
                }
            }
            animationLoops.push(requestAnimationFrame(draw));
        }
        draw();
    }

    // --- 1.6 Orbit (Tools orbiting center) ---
    function runOrbit(canvasId) {
        const canvas = document.getElementById(canvasId);
        if(!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width = canvas.parentElement.offsetWidth;
        const h = canvas.height = canvas.parentElement.offsetHeight;
        let t = 0;

        function draw() {
            ctx.fillStyle = C_BG; ctx.fillRect(0,0,w,h);

            // Center
            ctx.beginPath(); ctx.arc(w/2, h/2, 15, 0, 6.28); ctx.fillStyle = '#fff'; ctx.fill();

            // Orbits
            const count = isAI ? 12 : 3;
            const speed = isAI ? 0.02 : 0.005;

            for(let i=0; i<count; i++) {
                let r = 40 + (i*12);
                let angle = t * (i%2==0 ? speed : -speed) + (i);
                let x = w/2 + Math.cos(angle)*r;
                let y = h/2 + Math.sin(angle)*r;

                ctx.strokeStyle = '#333'; ctx.beginPath(); ctx.arc(w/2, h/2, r, 0, 6.28); ctx.stroke();
                ctx.beginPath(); ctx.arc(x, y, 4, 0, 6.28);
                ctx.fillStyle = isAI ? C_NEW : C_ACCENT;
                ctx.fill();
            }
            t++;
            animationLoops.push(requestAnimationFrame(draw));
        }
        draw();
    }

    // --- 2.2 Spiral (Time Compression) ---
    function runSpiral(canvasId) {
        const canvas = document.getElementById(canvasId);
        if(!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width = canvas.parentElement.offsetWidth;
        const h = canvas.height = canvas.parentElement.offsetHeight;
        let offset = 0;

        function draw() {
            ctx.fillStyle = C_BG; ctx.fillRect(0,0,w,h);

            let cx = w/2, cy = h/2;
            let coils = isAI ? 10 : 3; // More coils = tighter loops = faster
            let color = isAI ? C_NEW_SEC : C_ACCENT;

            ctx.beginPath();
            for(let i=0; i<100; i++) {
                let angle = 0.1 * i + offset;
                let r = 5 + (2 * angle);
                if(isAI) r = 5 + (0.5 * angle); // Tighter spiral

                let x = cx + Math.cos(angle) * r;
                let y = cy + Math.sin(angle) * r;
                if(i==0) ctx.moveTo(x,y);
                else ctx.lineTo(x,y);
            }
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.stroke();

            offset -= 0.1; // Animation speed
            animationLoops.push(requestAnimationFrame(draw));
        }
        draw();
    }

    // --- 2.6 Particle Flow (Throughput) ---
    function runParticles(canvasId) {
        const canvas = document.getElementById(canvasId);
        if(!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width = canvas.parentElement.offsetWidth;
        const h = canvas.height = canvas.parentElement.offsetHeight;

        let particles = [];

        function draw() {
            // Trail effect
            ctx.fillStyle = 'rgba(30,30,30,0.2)'; ctx.fillRect(0,0,w,h);

            // Spawn rate
            let spawnRate = isAI ? 0.8 : 0.1; // Much faster spawn in AI
            if(Math.random() < spawnRate) {
                particles.push({x: 0, y: h/2 + (Math.random()*40 - 20), vx: isAI? 8:2, c: isAI?C_NEW:C_ACCENT});
            }

            particles.forEach((p, index) => {
                p.x += p.vx;
                ctx.fillStyle = p.c;
                ctx.fillRect(p.x, p.y, 4, 4);
                if(p.x > w) particles.splice(index, 1);
            });

            animationLoops.push(requestAnimationFrame(draw));
        }
        draw();
    }

    // --- 3.2 Beeswarm (Backlog) ---
    function runBeeswarm(canvasId) {
        const canvas = document.getElementById(canvasId);
        if(!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width = canvas.parentElement.offsetWidth;
        const h = canvas.height = canvas.parentElement.offsetHeight;

        // Init 100 dots
        let dots = [];
        for(let i=0; i<100; i++) {
            dots.push({
                x: Math.random()*w,
                y: h - 20, // Start at bottom (backlog)
                targetY: h - 20,
                active: false
            });
        }

        function draw() {
            ctx.clearRect(0,0,w,h);

            // Logic: In AI mode, dots activate and move up (Completed)
            let activeCount = isAI ? 80 : 10;

            dots.forEach((d, i) => {
                if(i < activeCount) {
                    d.targetY = 50 + Math.random()*50; // Move to top
                    d.active = true;
                } else {
                    d.targetY = h - 50 + Math.random()*40; // Stay bottom
                    d.active = false;
                }

                // Lerp
                d.y += (d.targetY - d.y) * 0.05;

                ctx.fillStyle = d.active ? C_NEW_SEC : '#444';
                ctx.beginPath(); ctx.arc(d.x, d.y, 3, 0, 6.28); ctx.fill();
            });

            // Text labels
            ctx.fillStyle = '#888';
            ctx.fillText("Completed", 10, 40);
            ctx.fillText("Backlog / Neglected", 10, h-10);

            animationLoops.push(requestAnimationFrame(draw));
        }
        draw();
    }

    // --- 3.4 Heatmap (Repo Coverage) ---
    function runHeatmap(canvasId) {
        const canvas = document.getElementById(canvasId);
        if(!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width = canvas.parentElement.offsetWidth;
        const h = canvas.height = canvas.parentElement.offsetHeight;

        let cols = 20, rows = 10;
        let cellW = w/cols, cellH = h/rows;

        function draw() {
            ctx.clearRect(0,0,w,h);

            for(let i=0; i<cols; i++) {
                for(let j=0; j<rows; j++) {
                    let id = i*rows + j;
                    // AI lights up random corners (legacy code)
                    let lit = false;
                    if(isAI) {
                        // Random noise logic
                        lit = Math.sin(id * 99 + Date.now()/500) > 0;
                    } else {
                        // Only center lit
                        lit = (i > 5 && i < 15 && j > 2 && j < 8);
                    }

                    ctx.fillStyle = lit ? (isAI ? C_NEW : C_ACCENT) : '#2a2a2a';
                    ctx.fillRect(i*cellW + 1, j*cellH + 1, cellW-2, cellH-2);
                }
            }
            animationLoops.push(requestAnimationFrame(draw));
        }
        draw();
    }

</script>
</body>
</html>
```
