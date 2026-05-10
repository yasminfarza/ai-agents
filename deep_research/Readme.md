# 🔬 Deep Research Agent

A multi-agent deep research pipeline built with the **OpenAI Agents SDK**.  
Enter any research query, answer the clarifying questions, and receive a detailed, evaluated, and emailed report — fully orchestrated by a single `OrchestratorAgent`.

---

## Architecture Overview

```
User Query
    │
    ▼
[Input Guardrail] ── blocks harmful/off-topic queries
    │
    ▼
ClarificationAgent ──► 3 targeted questions ──► User answers
    │
    ▼
PlannerAgent ──► 5 tuned search queries
    │
    ▼
SearchAgent × 5 (parallel) ──► 5 web summaries
    │
    ▼
WriterAgent ──► Draft report (1000+ words, Markdown)
    │
    ▼
EvaluatorAgent ──► Score 1–10
    │
    ├── Score ≥ 7 ──► Accept
    └── Score < 7 ──► Rewrite (max 2 attempts) ──► Accept
    │
    ▼
[Output Guardrail] ── blocks harmful report content
    │
    ▼
EmailAgent ──► HTML email sent via SendGrid
    │
    ▼
Gradio UI ──► Streamed Markdown report
```

### Design Patterns Used

| Pattern | Where |
|---|---|
| **Guardrails** | Input + output safety checks on `OrchestratorAgent` |
| **Clarification before action** | `ClarificationAgent` asks 3 questions before any search |
| **Structured Outputs** | Every agent uses Pydantic models for reliable, typed responses |
| **Parallel tool calls** | 5 web searches run concurrently via `asyncio` |
| **Manager as Agent** | `OrchestratorAgent` uses `agents_as_tools` to coordinate all sub-agents |
| **Evaluator-Optimizer loop** | `EvaluatorAgent` scores the report; triggers rewrite if quality score < 7 |
| **Streaming** | `Runner.run_streamed()` streams tokens live to the Gradio UI |

---

## File Structure

```
├── app.py                  # Gradio UI — entry point
├── orchestratorAgent.py    # OrchestratorAgent
├── guardrails.py           # Input and output safety guardrails
├── clarification_agent.py  # Generates 3 clarifying questions
├── planner_agent.py        # Plans 5 targeted web searches
├── search_agent.py         # Executes a single web search + summarizes
├── writer_agent.py         # Writes the full Markdown report
├── evaluator_agent.py      # Scores the report and gives rewrite feedback
├── email_agent.py          # Converts report to HTML and sends via SendGrid
└── README.md
```

---

## Agents

### `ClarificationAgent`
Receives the raw user query and returns exactly **3 clarifying questions** targeting different dimensions — scope, audience, time frame, depth, or use-case. Answers are woven into the enriched prompt used by all downstream agents.

### `PlannerAgent`
Receives the enriched query (original + clarification answers) and outputs **5 specific web search queries**. Each query is distinct and directly motivated by the clarifications.

### `SearchAgent`
Executes a single web search using `WebSearchTool` and returns a concise 2-3 paragraph summary under 300 words. Called **5 times in parallel** for speed.

### `WriterAgent`
Receives all search summaries and writes a **detailed Markdown report** (1000+ words, 5-10 pages). Uses headers, subheaders, tables, and bullet points. Also self-assesses its own quality score.

### `EvaluatorAgent`
Critically evaluates the report across 6 dimensions: coverage, depth, structure, evidence, length, and clarity. Returns a **score out of 10**, a pass/fail decision, identified weaknesses, and specific rewrite instructions if score < 7.

### `EmailAgent`
Converts the final Markdown report into clean, styled **HTML** and sends it via SendGrid with an appropriate subject line.

### `OrchestratorAgent`
The top-level agent. Has all sub-agents registered as tools via `as_tool()` and `SearchAgent` as a handoff target. Coordinates the entire pipeline autonomously — including the evaluator-optimizer rewrite loop — from a single enriched prompt. Protected by input and output guardrails.

---

## Guardrails

Guardrails are safety checks that wrap the `OrchestratorAgent`. They run **before and after** the main pipeline, so bad input never wastes API calls and bad output never reaches the user.

### Input Guardrail — `research_input_guardrail`

Runs **before** the pipeline starts. Blocks queries that:
- Ask for instructions on creating weapons, drugs, or malware
- Request private/personal information about real individuals (doxxing)
- Facilitate illegal activities
- Are sexually explicit or involve minors inappropriately
- Are pure gibberish with no research intent

If blocked, the user sees a clear rejection message and no API calls are made downstream.

### Output Guardrail — `research_output_guardrail`

Runs **after** the report is written. Blocks reports that:
- Contain step-by-step instructions for creating dangerous items
- Include private information about real individuals
- Contain hate speech or targeted harassment

Both guardrails use `gpt-4o-mini` for fast, cheap classification and are configured to lean toward **allowing** borderline-but-legitimate research topics.

### How guardrails work in the code

```python
# guardrails.py
@input_guardrail
async def research_input_guardrail(ctx, agent, input) -> GuardrailFunctionOutput:
    ...
    return GuardrailFunctionOutput(
        output_info=decision,
        tripwire_triggered=not decision.is_safe,  # True = block
    )

# research_manager.py
orchestrator_agent = Agent(
    ...
    input_guardrails=[research_input_guardrail],
    output_guardrails=[research_output_guardrail],
)
```
---

## Evaluator-Optimizer Loop

```
WriterAgent produces draft
        │
EvaluatorAgent scores it (1–10)
        │
   score ≥ 7? ──► YES ──► Accept report
        │
       NO
        │
   attempt < 2? ──► YES ──► WriterAgent rewrites with feedback
        │
       NO ──► Accept anyway (best effort)
```

---

## Extending the Project

- **Add a `FileSearchTool`** to search your own documents alongside the web
- **Persist reports** to Google Drive or a database after each run
- **Swap `WebSearchTool`** for Tavily, Serper, or Brave for cost savings
- **Tighten guardrails** by adding domain-specific blocked topics
- **Add a `ComputerTool`** to screenshot relevant web pages for the report