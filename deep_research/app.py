"""
deep_research.py  —  Deep Research Agent UI
"""

import gradio as gr
from dotenv import load_dotenv
from agents import Runner, trace, gen_trace_id
from orchestrator_agent import orchestrator_agent
from clarification_agent import clarification_agent, ClarificationPlan

load_dotenv(override=True)


# ── Step 1: Generate clarifying questions ─────────────────────────────────────

async def get_clarifications(query: str):
    """
    Yields twice:
      1. Immediately — shows loading state
      2. After agent responds — shows the 3 question boxes
    """
    if not query.strip():
        yield (
            gr.update(visible=False, value="", label=""),   # q1
            gr.update(visible=False, value="", label=""),   # q2
            gr.update(visible=False, value="", label=""),   # q3
            gr.update(visible=False),                       # run_btn
            gr.update(visible=False),                       # status_box
            gr.update(value=""),                            # report
            None,                                           # state
        )
        return

    # Yield 1: immediate loading feedback
    yield (
        gr.update(visible=False, value="", label=""),
        gr.update(visible=False, value="", label=""),
        gr.update(visible=False, value="", label=""),
        gr.update(visible=False),
        gr.update(visible=True,  value="⏳ Generating clarifying questions…"),
        gr.update(value=""),
        None,
    )

    result = await Runner.run(clarification_agent, f"Query: {query}")
    plan: ClarificationPlan = result.final_output_as(ClarificationPlan)
    questions = [cq.question for cq in plan.questions]
    while len(questions) < 3:
        questions.append("Any additional context to share?")

    # Yield 2: show all 3 question boxes with real labels
    yield (
        gr.update(visible=True, value="", label=f"Q1: {questions[0]}"),
        gr.update(visible=True, value="", label=f"Q2: {questions[1]}"),
        gr.update(visible=True, value="", label=f"Q3: {questions[2]}"),
        gr.update(visible=True),
        gr.update(visible=True, value="✅ Answer the questions below, then click **Run Research**."),
        gr.update(value=""),
        questions,
    )


# ── Step 2: Run full pipeline ─────────────────────────────────────────────────

async def run_research(query: str, q1: str, q2: str, q3: str, questions: list):
    if not query.strip():
        yield "⚠️ Please enter a research query first."
        return

    lines = []
    for i, (q, a) in enumerate(zip(questions or [], [q1, q2, q3])):
        answer = a.strip() if a.strip() else "(not answered — use best judgement)"
        lines.append(f"  Q{i+1}: {q}\n  A{i+1}: {answer}")

    enriched_prompt = (
        f"Research query: {query}\n\n"
        f"Clarifications from the user:\n" + "\n".join(lines) + "\n\n"
        "Run the full research pipeline in order:\n"
        "1. Call clarify_query\n"
        "2. Call plan_searches with the enriched query\n"
        "3. Call search_web for EVERY search query returned — do not skip any\n"
        "4. Call write_report with the enriched query AND all search summaries\n"
        "5. Call evaluate_report — if score < 7, call write_report again with feedback\n"
        "6. Call send_report_email with the final report\n"
        "7. Return the complete final Markdown report as your output"
    )

    trace_id = gen_trace_id()
    trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"

    accumulated = f"> 🔍 **[View Live Trace]({trace_url})**\n\n---\n\n"
    yield accumulated

    with trace("Deep Research", trace_id=trace_id):
        stream = Runner.run_streamed(orchestrator_agent, enriched_prompt)
        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                delta = getattr(event.data, "delta", None)
                if delta:
                    accumulated += delta
                    yield accumulated


# ── Custom CSS ────────────────────────────────────────────────────────────────

CSS = """
/* ── Global ── */
body, .gradio-container { font-family: 'Inter', system-ui, sans-serif; }
.gradio-container { max-width: 860px !important; margin: 0 auto !important; padding: 0 16px; }
footer { display: none !important; }

/* ── Hero header ── */
#hero {
    background: linear-gradient(135deg, #0369a1 0%, #4f46e5 100%);
    border-radius: 14px;
    padding: 36px 40px 32px;
    margin-bottom: 28px;
    color: white;
}
#hero h1 { font-size: 1.9rem; font-weight: 700; margin: 0 0 10px; color: white !important; }
#hero p  { font-size: 0.95rem; margin: 0; opacity: 0.88; color: white !important; line-height: 1.5; }

/* ── Step badges ── */
.step-badge {
    display: inline-block;
    background: #0ea5e9;
    color: white;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 99px;
    margin-bottom: 10px;
}

/* ── Panel cards ── */
.panel {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px 24px 24px;
    margin-bottom: 16px;
    background: white;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* ── Status bar ── */
#status-bar {
    border-left: 4px solid #0ea5e9;
    background: #f0f9ff;
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    font-size: 14px;
    margin-bottom: 12px;
}

/* ── Report area ── */
#report-area {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 28px 32px;
    background: white;
    min-height: 160px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    font-size: 15px;
    line-height: 1.7;
}

/* ── Buttons ── */
.big-btn { width: 100% !important; margin-top: 12px !important; }
"""


# ── Gradio UI ─────────────────────────────────────────────────────────────────

with gr.Blocks(css=CSS, theme=gr.themes.Soft(primary_hue="sky", neutral_hue="slate")) as ui:

    questions_state = gr.State(None)

    # ── Hero ──────────────────────────────────────────────────────────────────
    gr.HTML("""
    <div id="hero">
        <h1>🔬 Deep Research Agent</h1>
        <p>
            Powered by a multi-agent pipeline: clarification → parallel web search →
            report writing → quality evaluation → email delivery.<br>
            Enter a topic, answer 3 quick questions, and receive a detailed researched report.
        </p>
    </div>
    """)

    # ── Step 1 ────────────────────────────────────────────────────────────────
    with gr.Group(elem_classes="panel"):
        gr.HTML('<span class="step-badge">Step 1 — Research Query</span>')
        query_box = gr.Textbox(
            label="What would you like to research?",
            placeholder="e.g.  Latest AI Agent frameworks in 2025",
            lines=3,
        )
        clarify_btn = gr.Button(
            "✨  Get Clarifying Questions",
            variant="secondary",
            elem_classes="big-btn",
        )

    # ── Status bar ────────────────────────────────────────────────────────────
    status_box = gr.Markdown(
        value="",
        visible=False,
        elem_id="status-bar",
    )

    # ── Step 2 ────────────────────────────────────────────────────────────────
    with gr.Group(elem_classes="panel"):
        gr.HTML('<span class="step-badge">Step 2 — Clarifying Questions</span>')
        q1_box = gr.Textbox(label="", lines=2, visible=False)
        q2_box = gr.Textbox(label="", lines=2, visible=False)
        q3_box = gr.Textbox(label="", lines=2, visible=False)
        run_btn = gr.Button(
            "🚀  Run Research",
            variant="primary",
            visible=False,
            elem_classes="big-btn",
            size="lg",
        )

    # ── Step 3 ────────────────────────────────────────────────────────────────
    gr.HTML('<span class="step-badge">Step 3 — Report</span>')
    report_output = gr.Markdown(
        value="_Your report will appear here once the pipeline completes…_",
        elem_id="report-area",
    )

    # ── Event wiring ──────────────────────────────────────────────────────────
    # IMPORTANT: order must exactly match the yield tuple in get_clarifications
    clarify_outputs = [
        q1_box,          # 0
        q2_box,          # 1
        q3_box,          # 2
        run_btn,         # 3
        status_box,      # 4
        report_output,   # 5
        questions_state, # 6
    ]

    clarify_btn.click(
        fn=get_clarifications,
        inputs=[query_box],
        outputs=clarify_outputs,
    )
    query_box.submit(
        fn=get_clarifications,
        inputs=[query_box],
        outputs=clarify_outputs,
    )
    run_btn.click(
        fn=run_research,
        inputs=[query_box, q1_box, q2_box, q3_box, questions_state],
        outputs=[report_output],
    )

if __name__ == "__main__":
    ui.launch()