# ── Orchestrator Agent (agents_as_tools + handoffs) ─────────────────────────
#
# This is the "Manager as Agent" pattern from the course.  The orchestrator
# agent has every sub-agent available as a callable tool via as_tool(), and
# can also hand off to search_agent directly for long fan-out tasks.
#
# In practice the ResearchManager class above gives you fine-grained async
# control with streaming; the OrchestratorAgent below demonstrates the
# pattern for completeness and can be used for non-streaming, single-call use.
import os
from agents import Agent

from clarification_agent import clarification_agent
from guardrails import research_input_guardrail, research_output_guardrail
from planner_agent import planner_agent
from search_agent import search_agent
from writer_agent import writer_agent
from evaluator_agent import evaluator_agent
from email_agent import email_agent


_clarification_tool = clarification_agent.as_tool(
    tool_name="clarify_query",
    tool_description=(
        "Given a raw research query, return 3 clarifying questions that will make "
        "the research more precise."
    ),
)

_planner_tool = planner_agent.as_tool(
    tool_name="plan_searches",
    tool_description=(
        "Given an enriched query (original query + clarification answers), "
        "return a list of specific web search queries to run."
    ),
)

_search_tool = search_agent.as_tool(
    tool_name="search_web",
    tool_description=(
        "Search the web for a single search term and return a concise summary. "
        "Call this tool once per search query. Call it multiple times for multiple queries."
    ),
)

_writer_tool = writer_agent.as_tool(
    tool_name="write_report",
    tool_description=(
        "Given the original query, clarifications, and search result summaries, "
        "write a detailed Markdown research report."
    ),
)

_evaluator_tool = evaluator_agent.as_tool(
    tool_name="evaluate_report",
    tool_description=(
        "Given the query and a draft report, evaluate its quality (score 1-10) "
        "and provide rewrite instructions if score < 7."
    ),
)

_email_tool = email_agent.as_tool(
    tool_name="send_report_email",
    tool_description="Convert a Markdown report to HTML and send it by email.",
)

ORCHESTRATOR_INSTRUCTIONS = """
You are a deep-research orchestrator. Coordinate your tools to produce a high-quality research report.
 
Follow this exact pipeline:
 
1. Call clarify_query with the user's raw research query.
   Use the returned questions together with the user's provided answers to build context.
 
2. Call plan_searches with the enriched query (original query + clarification Q&A).
   This returns a list of search queries to run.
 
3. For EACH search query in the plan, call search_web once.
   Collect ALL the summaries before moving on.
 
4. Call write_report passing the enriched query and ALL collected search summaries.
 
5. Call evaluate_report on the draft report:
   - If score >= 7: proceed to step 6.
   - If score < 7: call write_report again, appending the evaluator feedback to the input.
     Repeat at most 2 times total, then proceed regardless.
 
6. Call send_report_email with the final report markdown.
 
7. Return the final Markdown report as your response.
 
Important rules:
- Never skip a step.
- Always complete ALL search_web calls before calling write_report.
- Always call evaluate_report before send_report_email.
- Do not hand off to any agent — use only your tools.
"""

orchestrator_agent = Agent(
    name="OrchestratorAgent",
    instructions=ORCHESTRATOR_INSTRUCTIONS,
    tools=[
        _clarification_tool,
        _planner_tool,
        _search_tool,       
        _writer_tool,
        _evaluator_tool,
        _email_tool,
    ],
    handoffs=[email_agent],
    model=os.environ.get("MODEL"),   # use a stronger model for the orchestrator
    input_guardrails=[research_input_guardrail],
    output_guardrails=[research_output_guardrail],
)
