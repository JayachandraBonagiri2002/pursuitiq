# PursuitIQ - Demo Presentation (3 Minutes, 4 Slides)

---

## SLIDE 1: The Problem (30 seconds)

**Title:** RFP Research Takes Days. Strategy Time Gets Squeezed.

**Content (simple, honest):**

When a new RFP lands, the pursuit team needs to:
- Research the client (news, leadership, priorities, hiring patterns)
- Analyze competitors (who's bidding, what they've won recently, their strengths)
- Build pricing (gather current cloud rates, estimate costs, set margins)
- Understand the RFP (hidden requirements, evaluation weights, compliance needs)

**The problem:** This research takes **3-5 days** of manual work across multiple people. By the time research is done, there's little time left for **strategy and quality writing** — the things that actually win deals.

**Speaker Notes:**
"When an enterprise RFP comes in, the first thing the team does is research — who's the client, who are we competing against, what should we price at, what are the hidden requirements. This research takes 3-5 days of manual effort — searching the web, reading procurement portals, pulling pricing sheets, reviewing past deals. The problem isn't that teams can't do it. They can. But it eats the time they should be spending on strategy and writing a compelling response."

---

## SLIDE 2: What PursuitIQ Does (30 seconds)

**Title:** PursuitIQ — Research Acceleration for Pursuit Teams

**Tagline:** 11 AI agents do your research in 12 minutes. You focus on winning.

**What it delivers (be specific and honest):**

| What PursuitIQ Gives You | How It Helps |
|---|---|
| **RFP Breakdown** | Requirements, disqualifiers, evaluation criteria — structured and clear |
| **Client Intelligence** | Recent news, leadership changes, hiring patterns, strategic signals — from live web |
| **Competitor Analysis** | Who's likely bidding, what they've recently won, their predicted approach |
| **Pricing Benchmark** | Real-time Azure/AWS cloud rates + cost models for solution options |
| **Win Themes** | Suggested differentiators based on client needs vs. competitor weaknesses |
| **Proposal Starting Point** | Structured draft pulling all intelligence together — a starting point, not final output |

**What it does NOT do:**
- Replace your team's judgment or relationships
- Generate a submission-ready proposal
- Make the bid decision for you

**Speaker Notes:**
"PursuitIQ has 11 AI agents that do the research phase for you — in 12 minutes instead of days. It searches the live web for client signals and competitor moves. It pulls real-time cloud pricing from Azure and AWS. It reviews the RFP and surfaces hidden requirements you might miss. It gives you a structured starting point for your proposal. Your team still decides, still strategizes, still writes the final response — but now they start with intelligence instead of a blank page."

---

## SLIDE 3: LIVE DEMO (90 seconds)

**Title:** [Switch to browser]

**Demo Script:**

**0:00 - 0:10 | Start**
- Open app → "Let me show you what happens when an RFP comes in"
- Click "Run Demo" (or upload a prepared short RFP)

**0:10 - 0:30 | Show Agents Working**
- Point to pipeline tracker: "11 agents are working in parallel — one is breaking down the RFP, one is searching the web for client news, one is analyzing competitors, one is pulling live cloud pricing..."
- "This would normally take your team 3-5 days. Watch."

**0:30 - 1:20 | Walk Through the Intelligence**

Show each tab (spend time on the VALUE, not the tech):

1. **Overview (10 sec):** "Here's the RFP broken down — key requirements, disqualifiers your team might have missed, evaluation criteria with weights."

2. **Client Intel (15 sec):** "The agent searched the live web — found that the client just hired a new CTO from AWS, they have open cloud architect roles, their last earnings call mentioned cost optimization. Your team would find this eventually — but now they have it in minutes."

3. **Competitor (20 sec):** "Here's the competitive landscape — who's likely bidding based on their recent wins and hiring patterns. And here's a simulated approach for each competitor — how they'd likely position. Not perfect, but useful for your strategy session."

4. **Pricing (10 sec):** "Solution options with real Azure and AWS pricing pulled just now — not last quarter's spreadsheet. Your pricing team can start from here instead of spending a day gathering rates."

5. **Draft (5 sec):** "And a proposal structure pulling all the intelligence together — your writers start with substance, not a blank page."

**1:20 - 1:30 | Close Demo**
- "12 minutes. Your team now has a head start of days."

---

## SLIDE 4: How It Works + OpenAI Tech (30 seconds)

**Title:** Built on OpenAI — 11 Agents, 7 Platform Features

**Architecture (simplified, judge-friendly):**

```
Upload RFP
    │
    ▼
┌─────────────────────────────────────────────────┐
│  PLANNER AGENT — decides execution strategy      │
└──────────────────────┬──────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│  AGENT 1: RFP Decomposer (Structured Outputs)    │
└──────────────────────┬───────────────────────────┘
                       ▼
    ┌──────────────────┼──────────────────┐
    ▼                  ▼                  ▼
┌────────┐      ┌──────────┐      ┌───────────┐
│Agent 2 │      │ Agent 3  │      │  Agent 4  │   ← PARALLEL
│Win Intel│      │Client Web│      │Competitor │
│RAG/file │      │ Search   │      │Web Search │
│ search  │      │          │      │           │
└────┬───┘      └─────┬────┘      └─────┬─────┘
     └─────────────────┼─────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│  AGENT 5: Pricing (Live Azure/AWS API rates)      │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│  AGENT 6: Draft Generator (Codex / GPT-5)         │
└──────────────────────┬───────────────────────────┘
                       ▼
┌────────────┐  ┌─────────────┐  ┌─────────────┐
│Quality Gate│  │Deal Pattern │  │ Ghost Bid   │
│+ Reflection│  │  Matching   │  │ Simulation  │
└────────────┘  └─────────────┘  └─────────────┘
                       ▼
              Pursuit Intelligence
             Ready for Your Team
```

**OpenAI Features (bottom of slide as a strip):**

Structured Outputs | Web Search (Responses API) | File Search (RAG) | Vector Stores | Codex GPT-5 | Reasoning Control | Multi-Model Routing

**Speaker Notes:**
"11 agents built entirely on OpenAI. We use Structured Outputs for reliable agent-to-agent communication. The Responses API with web search for live intelligence. File search and vector stores for RAG over historical deals. Codex for GPT-5 proposal drafting at zero cost. And reasoning control — high effort for critical analysis, medium for research breadth. All autonomous, all in 12 minutes. Thank you."

---

## DEMO PREP CHECKLIST

- [ ] Pre-run a pursuit 5 min before slot (have completed results as backup)
- [ ] App running, browser on landing page, dark mode, 90% zoom
- [ ] Prepare a short RFP PDF (1-2 pages) for quick processing
- [ ] Test internet (web search needs it)
- [ ] Have a COMPLETED pursuit loaded — if live demo is slow, say "let me show one that just finished"
- [ ] Practice with timer at least 5 times
- [ ] Close all tabs/notifications

---

## JUDGE Q&A — HONEST ANSWERS

**"Would a company actually use this?"**
"Yes — not as a replacement for their team, but as research acceleration. The same way a financial analyst uses Bloomberg terminal instead of manually searching SEC filings. PursuitIQ gives the pursuit team a 3-5 day head start on research so they can focus on strategy and quality writing."

**"Isn't the proposal just hallucinated?"**
"The proposal draft is a starting point, not a final submission. The real value is the intelligence — client signals from live web search, competitor analysis from real data, pricing from actual Azure and AWS rates. The quality gate also verifies claims against the source data."

**"How is this different from ChatGPT?"**
"Three things. First, 11 specialized agents running in parallel — not one generic prompt. Second, tool use — agents search the live web, query vector stores, pull real pricing APIs autonomously. Third, structured outputs ensure reliable data flow between agents — this is an engineering system, not a chat session."

**"What OpenAI tech are you using?"**
"Seven platform features: Structured Outputs for type-safe agent communication, Responses API with web search and file search, Vector Stores for RAG, Codex CLI for GPT-5 at zero cost, reasoning effort control per agent, and multi-model routing."

**"How do you handle hallucination?"**
"Web search grounds claims in real data. The quality gate agent independently verifies major claims. The reflection loop re-generates if quality scoring fails. And structured outputs enforce valid formats — agents can't return garbage."

**"What's the cost?"**
"Under $5 per full run — 11 agents, all the research, all the analysis. Compare that to days of manual team effort."
