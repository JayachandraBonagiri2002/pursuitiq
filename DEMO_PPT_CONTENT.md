# PursuitIQ - Final Demo Presentation (3 Minutes, 4 Slides)

---

## SLIDE 1: Hook + Problem (30 seconds)

**Title:** What If You Had 11 AI Researchers Working on Every Deal?

**Visual idea:** Split screen — LEFT: one person drowning in tabs, PDFs, spreadsheets. RIGHT: PursuitIQ dashboard with all intelligence ready.

**3 lines only (big text, visual):**

> Enterprise pursuit teams spend **3-5 days** gathering intelligence before they can even start writing.
>
> Client research. Competitor tracking. Pricing data. RFP analysis. All manual. All slow.
>
> **PursuitIQ gives your team 11 AI agents that do all of it in 12 minutes.**

**Speaker Notes:**
"Imagine you're on a pursuit team. A new RFP drops — 80 pages. Before you can write a single line of your proposal, you need to research the client, figure out who you're competing against, gather current cloud pricing, and decode what the evaluators actually care about. That takes 3-5 days. PursuitIQ does all of that research in 12 minutes using 11 AI agents running in parallel on OpenAI. Let me show you."

---

## SLIDE 2: What You Get in 12 Minutes (30 seconds)

**Title:** 12 Minutes. Zero Manual Research. Full Intelligence.

**Visual idea:** 6 cards/panels with icons — looks like a dashboard preview

**Card 1 — RFP Decoded**
Every requirement, disqualifier, evaluation weight, and deadline — extracted and structured. Nothing missed.

**Card 2 — Client Signals (LIVE)**
Agent searches the web RIGHT NOW — leadership changes, hiring patterns, earnings signals, tech strategy. Not last month's data.

**Card 3 — Competitor Playbook**
Who's bidding. What they've won recently. How they'll likely position. Simulated ghost bids showing their probable approach.

**Card 4 — Live Pricing**
Real-time Azure and AWS rates — pulled from APIs at the moment of analysis. 3 solution options with actual cost breakdowns.

**Card 5 — Win Strategy**
Where competitors are weak. What the client actually needs. Your killer differentiators. Suggested win themes.

**Card 6 — Proposal Starting Point**
All intelligence synthesized into a structured draft. Your writers start with substance, not a blank page.

**Bottom line (on slide):**
> "Your team still owns the strategy. Still writes the final proposal. But now they start with days of research already done."

**Speaker Notes:**
"In 12 minutes, your team gets six things. The RFP completely broken down — no hidden disqualifier missed. Client intelligence from the live web — not a static report, real-time signals. Competitor analysis with simulated approaches. Pricing built on today's Azure and AWS rates. A win strategy based on where competitors are weak. And a structured proposal starting point so your writers aren't starting from scratch. Your team still decides, still writes, still strategizes — they just start days ahead."

---

## SLIDE 3: LIVE DEMO (90 seconds — THIS IS WHERE YOU WIN)

**Title:** [Switch to browser — full screen]

**THE GOLDEN RULE: Don't explain the tech during demo. Show the VALUE. Let them feel the "wow."**

---

### Demo Script (practice this with a timer):

**0:00 - 0:10 | Open + Start**
- Browser is already open on landing page
- Say: "Let me run this on a real RFP."
- Click "Run Demo" (or upload your prepared 2-page RFP)

**0:10 - 0:30 | Agents Working (point at the pipeline tracker)**
- "11 agents just started. Agent 1 is decomposing the RFP. Now 2, 3, 4 launched in parallel — that's three agents simultaneously searching our deal history, the live web for client news, and competitor intelligence."
- "This is happening in real-time. No pre-cached results."
- If it's still running, keep talking: "Each agent has its own tools — web search, file search, pricing APIs — they choose what to use."

**0:30 - 0:50 | THE WOW MOMENT — Client Intelligence Tab**
- Click Client Intel tab
- "Look at this — the agent just searched the web and found: [read an actual finding from the output, e.g., 'Client hired a VP of Cloud from AWS three weeks ago. They have 5 open DevOps roles. Their CEO mentioned cost optimization in last earnings call.']"
- "Your team would find this eventually. But this took 45 seconds."

**0:50 - 1:10 | THE STRATEGY MOMENT — Competitor Tab**
- Click Competitor tab
- "Here's the competitive landscape. [Read top competitor name] — here's what they've won recently, their likely positioning, and here's a simulated ghost bid showing how they'd probably approach this."
- "This isn't fantasy. It's based on their actual wins, hiring patterns, and public moves."

**1:10 - 1:20 | Pricing Tab (quick)**
- Click Pricing tab
- "Three solution options. Pricing pulled from Azure and AWS APIs — these are today's rates, not last quarter's spreadsheet."

**1:20 - 1:30 | Close Demo**
- "All of this — 12 minutes. Your team now has a 3-day head start. They focus on strategy and winning, not researching."

---

### BACKUP PLAN (if live demo is slow):
Have a COMPLETED pursuit already loaded. If agents take too long, say:
"Let me show you one that just finished 2 minutes ago — same pipeline, same process."
Then walk through the tabs.

---

## SLIDE 4: Under the Hood — OpenAI Agentic Architecture (30 seconds)

**Title:** 11 Agents. 7 OpenAI Features. Fully Autonomous.

**Visual: Clean architecture flow (use boxes + arrows in PowerPoint, NOT ASCII)**

```
Design this in PowerPoint as colored boxes with arrows:

[RFP Upload]
      ↓
[Planner Agent] — "Decides how to approach this RFP"
      ↓
[Agent 1: RFP Decomposer] — Structured Outputs, reasoning: HIGH
      ↓
┌─────────────┬─────────────┬─────────────┐
↓             ↓             ↓             
[Agent 2]     [Agent 3]     [Agent 4]     ← PARALLEL
Win Intel     Client Intel  Competitor    
file_search   web_search    web_search    
(RAG)         (live web)    (live web)    
└─────────────┴─────────────┴─────────────┘
      ↓
[Agent 5: Pricing] — Live Azure/AWS API + reasoning: HIGH
      ↓
[Agent 6: Draft] — Codex GPT-5 (zero cost)
      ↓
┌─────────────┬─────────────┬─────────────┐
[Quality Gate] [Deal Pattern] [Ghost Bid]
 Reflection    Matching       Simulation
 Loop
└─────────────┴─────────────┴─────────────┘
      ↓
[Intelligence Ready — Team Takes Over]
```

**OpenAI Tech Strip (bottom of slide, horizontal bar):**

| Structured Outputs | Web Search | File Search + RAG | Vector Stores | Codex GPT-5 | Reasoning Control | Multi-Model |
|---|---|---|---|---|---|---|

**Speaker Notes:**
"Under the hood — 11 agents on OpenAI. Planner sets the strategy. Agent 1 decomposes the RFP using structured outputs. Three agents run in parallel — one does RAG over 100 past deals using file search, two search the live web for client and competitor intelligence. Agent 5 builds pricing from real Azure and AWS API calls. Agent 6 uses Codex — that's GPT-5 at zero API cost — to generate the proposal structure. Then quality gate verifies claims, pattern matching compares against historical deals, and ghost bid simulates competitor approaches. Seven OpenAI platform features. Fully autonomous. Twelve minutes. Thank you."

---

## TIMING SUMMARY

| Slide | Time | What Judges Remember |
|---|---|---|
| 1. Hook | 0:00 - 0:30 | "3-5 days → 12 minutes" |
| 2. What You Get | 0:30 - 1:00 | "Live web intel, ghost bids, real pricing" |
| 3. LIVE DEMO | 1:00 - 2:30 | **The client intel wow moment + ghost bid** |
| 4. Architecture | 2:30 - 3:00 | "11 agents, 7 OpenAI features, autonomous" |

---

## WHAT WINS HACKATHONS (keep in mind)

1. **Live demo that works** — Nothing beats seeing real output. Practice until you can do it with your eyes closed.
2. **One "wow" moment** — When you show live client intel that the agent JUST found from the web. That's your moment. Pause on it.
3. **Honest framing** — "We accelerate research, your team still wins the deal" is more believable than "AI replaces your sales team."
4. **Technical depth on demand** — Don't dump architecture in the main flow. Flash it. If judges ask "how," you have the answer.

---

## DEMO PREP CHECKLIST

- [ ] Pre-run a pursuit 5 min before slot (completed backup ready)
- [ ] App running on localhost, browser full-screen on landing page
- [ ] Dark mode ON (looks better on projector)
- [ ] Zoom browser to 90% so full dashboard fits
- [ ] Short RFP PDF ready (1-2 pages = faster processing)
- [ ] Internet tested and working (web search needs it)
- [ ] All other tabs/apps/notifications CLOSED
- [ ] **Practice 5 times with a timer. If you go over 3 min even once, cut words.**

---

## JUDGE Q&A — SHORT, CONFIDENT ANSWERS

**"How is this different from ChatGPT?"**
"ChatGPT is one model, one prompt. PursuitIQ is 11 specialized agents with their own tools — web search, file search, pricing APIs — running in parallel. The output is structured, verified by a quality gate, and grounded in live data. It's an engineering system, not a chat."

**"Would companies actually use this?"**
"Not to replace their team — to accelerate the research phase. Same way analysts use Bloomberg instead of manually reading SEC filings. The team still decides, still writes, still owns the relationship."

**"What about hallucination?"**
"Three layers: web search grounds claims in real data, quality gate verifies independently, reflection loop re-generates if it fails. Plus structured outputs between agents — no garbage in, no garbage out."

**"What's the cost?"**
"Under $5 per run for 11 agents doing full research. Compare that to 3-5 days of manual team effort."

**"Why 11 agents instead of one big prompt?"**
"Speed — three agents searching in parallel. Specialization — each has the right tools and reasoning level. Reliability — structured outputs between agents means no parsing failures. And quality control — separate agents verify what other agents produce."
