"""
research_manager.py

Enhanced Deep Research orchestrator.

Architecture:
─────────────────────────────────────────────────────
  OrchestratorAgent
    ├── agents_as_tools:
    │     • clarification_tool  (ClarificationAgent)
    │     • planner_tool        (PlannerAgent)
    │     • search_tool         (SearchAgent  — called N times in parallel)
    │     • writer_tool         (WriterAgent)
    │     • evaluator_tool      (EvaluatorAgent)
    │     • email_tool          (EmailAgent)
    └── handoff targets (for specialised, long-running sub-flows):
          • search_agent        (direct handoff for multi-search fan-out)
─────────────────────────────────────────────────────

Evaluator-Optimizer loop:
  Writer produces a report → Evaluator scores it.
  If score < QUALITY_THRESHOLD the writer is called again with the
  evaluator's rewrite instructions.  Max MAX_REWRITE_ATTEMPTS rewrites.
"""

import asyncio
from agents import (
    Agent,
    Runner,
    trace,
    gen_trace_id
)

from clarification_agent import clarification_agent, ClarificationPlan
from planner_agent import planner_agent, WebSearchPlan, WebSearchItem
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from evaluator_agent import evaluator_agent, EvaluationResult
from email_agent import email_agent

# ── tuneable constants ──────────────────────────────────────────────────────
QUALITY_THRESHOLD = 7          # minimum evaluator score to accept a report
MAX_REWRITE_ATTEMPTS = 1       # how many times we let the writer try again
# ───────────────────────────────────────────────────────────────────────────


class ResearchManager:
    """
    Orchestrates the full deep-research pipeline, yielding status strings
    (for the Gradio streaming UI) and finally the finished Markdown report.
    """

    # ── public entry point ─────────────────────────────────────────────────

    async def run(self, query: str, clarification_answers: dict[str, str] | None = None):
        """
        Main pipeline generator.  Yields status strings, then the final report.

        Parameters
        ----------
        query : str
            The raw user research query.
        clarification_answers : dict[str, str] | None
            Mapping of clarifying question → user's answer.
            If None, clarification questions are generated but not answered
            (useful for a single-shot headless call).
        """
        trace_id = gen_trace_id()

        with trace("Deep Research Trace", trace_id=trace_id):
            yield f"🔍 Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n"

            # ── Step 1: Clarification ─────────────────────────────────────
            yield "💬 Generating clarifying questions…"
            clarification_plan = await self._clarify(query)
            questions_text = "\n".join(
                f"  {i+1}. {q.question}"
                for i, q in enumerate(clarification_plan.questions)
            )
            yield f"**Clarifying questions asked:**\n{questions_text}"  # Show the clarifying questions to the user (for streaming UI) using generator (yield)

            # Build the enriched query string
            enriched_query = self._build_enriched_query(
                query, clarification_plan, clarification_answers
            )
            
            print("enriched_query", enriched_query)  # Debug print to verify enriched query content

            # ── Step 2: Plan searches ─────────────────────────────────────
            yield "📋 Planning searches based on your clarifications…"
            search_plan = await self._plan(enriched_query)
            print("search_plan", search_plan)  # Debug print to verify search plan content
            yield f"📌 {len(search_plan.searches)} searches planned."

            # ── Step 3: Execute searches (parallel) ───────────────────────
            yield "🌐 Running web searches in parallel…"
            search_results = await self._search_all(search_plan)
            yield f"✅ {len(search_results)} search results gathered."

            # ── Step 4: Write report (with Evaluator-Optimizer loop) ──────
            yield "✍️  Writing report…"
            report, eval_result, attempt = await self._write_with_eval_loop(
                enriched_query, search_results
            )
            score_emoji = "🟢" if eval_result.quality_score >= 8 else "🟡"
            yield (
                f"{score_emoji} Report accepted after {attempt} attempt(s). "
                f"Quality score: {eval_result.quality_score}/10"
            )

            # ── Step 5: Email the report ──────────────────────────────────
            yield "📧 Sending report by email…"
            await self._email(report)
            yield "📬 Email sent!"

            # ── Final: stream the report itself ───────────────────────────
            yield "\n---\n"
            yield report.markdown_report

    # ── private pipeline steps ─────────────────────────────────────────────

    async def _clarify(self, query: str) -> ClarificationPlan:
        # Get the clarification questions from the agent
        result = await Runner.run(clarification_agent, f"Query: {query}")
        return result.final_output_as(ClarificationPlan)

    async def _plan(self, enriched_query: str) -> WebSearchPlan:
        result = await Runner.run(planner_agent, enriched_query)
        return result.final_output_as(WebSearchPlan)

    async def _search_all(self, search_plan: WebSearchPlan) -> list[str]:
        tasks = [
            asyncio.create_task(self._search_one(item))
            for item in search_plan.searches
        ]
        results = []
        num_done = 0
        for coro in asyncio.as_completed(tasks):
            result = await coro
            num_done += 1
            print(f"  Search {num_done}/{len(tasks)} done")
            if result:
                results.append(result)
        return results

    async def _search_one(self, item: WebSearchItem) -> str | None:
        inp = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, inp)
            return str(result.final_output)
        except Exception as exc:
            print(f"  ⚠️  Search failed for '{item.query}': {exc}")
            return None

    async def _write_with_eval_loop(
        self,
        enriched_query: str,
        search_results: list[str],
    ) -> tuple[ReportData, EvaluationResult, int]:
        """
        Evaluator-Optimizer pattern:
        Write → Evaluate → rewrite if score < threshold (up to MAX_REWRITE_ATTEMPTS).
        Returns (final_report, final_evaluation, attempt_number).
        """
        base_input = (
            f"Original query + clarifications:\n{enriched_query}\n\n"
            f"Summarized search results:\n{search_results}"
        )
        writer_input = base_input
        attempt = 0

        while True:
            attempt += 1
            print(f"  Writing report (attempt {attempt})…")

            # Write
            write_result = await Runner.run(writer_agent, writer_input)
            report: ReportData = write_result.final_output_as(ReportData)

            # Evaluate
            print(f"  Evaluating report…")
            eval_input = (
                f"Original query + clarifications:\n{enriched_query}\n\n"
                f"Report to evaluate:\n{report.markdown_report}"
            )
            eval_result_raw = await Runner.run(evaluator_agent, eval_input)
            evaluation: EvaluationResult = eval_result_raw.final_output_as(EvaluationResult)
            
            print("evaluation", evaluation)  # Debug print to verify evaluation content

            print(
                f"  Evaluator score: {evaluation.quality_score}/10 "
                f"| passes={evaluation.passes}"
            )

            # Accept or retry
            if evaluation.passes or attempt >= MAX_REWRITE_ATTEMPTS:
                if not evaluation.passes:
                    print(
                        f"  ⚠️  Max rewrite attempts reached. "
                        f"Accepting score {evaluation.quality_score}/10."
                    )
                return report, evaluation, attempt

            # Build a richer prompt for the next write attempt
            weaknesses = "\n".join(f"- {w}" for w in evaluation.weaknesses)
            writer_input = (
                f"{base_input}\n\n"
                f"--- PREVIOUS ATTEMPT FEEDBACK (attempt {attempt}) ---\n"
                f"Quality score: {evaluation.quality_score}/10\n"
                f"Weaknesses identified:\n{weaknesses}\n\n"
                f"Rewrite instructions:\n{evaluation.rewrite_instructions}\n"
                f"--- END FEEDBACK ---\n\n"
                f"Please rewrite the report addressing all the weaknesses above."
            )
            print(f"  🔄 Requesting rewrite (attempt {attempt + 1})…")

    async def _email(self, report: ReportData) -> None:
        await Runner.run(email_agent, report.markdown_report)

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _build_enriched_query(
        query: str,
        plan: ClarificationPlan,
        answers: dict[str, str] | None,
    ) -> str:
        """
        Combine the original query with clarification Q&A pairs into a
        single enriched context string for the planner and writer.
        """
        lines = [f"Research query: {query}", "", "Clarifications:"]
        print("Answers:", answers)
        for i, cq in enumerate(plan.questions):
            print("  Clarifying question:", cq.question)
            answer = (answers or {}).get(cq.question, "(not answered — use best judgement)")
            print("  Answer:", answer)
            lines.append(f"  Q{i+1}: {cq.question}")
            lines.append(f"  A{i+1}: {answer}")
        return "\n".join(lines)
