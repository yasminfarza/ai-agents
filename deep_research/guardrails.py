"""
guardrails.py

Input and output guardrails for the Deep Research Agent.

- Input guardrail:  blocks queries that are harmful, illegal, or off-topic
- Output guardrail: blocks reports that contain harmful or inappropriate content

Guardrails run BEFORE the main pipeline (input) and AFTER the report is
written (output), so they never waste search/write API calls on bad input,
and never surface dangerous output to the user.
"""
import os
from agents import (
    Agent,
    Runner,
    input_guardrail,
    output_guardrail,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
)
from pydantic import BaseModel


# ── Shared schema ─────────────────────────────────────────────────────────────

class GuardrailDecision(BaseModel):
    is_safe: bool
    reason: str   # shown to the user if blocked


# ── Input Guardrail ───────────────────────────────────────────────────────────

INPUT_GUARDRAIL_INSTRUCTIONS = """
You are a safety classifier for a deep research tool.

Decide whether the user's research query is SAFE to process.

Mark as UNSAFE (is_safe=False) if the query:
- Asks for instructions on creating weapons, drugs, malware, or explosives
- Requests personal/private information about real individuals (doxxing)
- Promotes or facilitates illegal activities
- Is sexually explicit or involves minors in any inappropriate way
- Is designed to generate misinformation or propaganda
- Is completely nonsensical (gibberish) with no research intent

Mark as SAFE (is_safe=True) if the query:
- Is a legitimate research topic, even if sensitive (e.g. "history of chemical warfare")
- Is academic, technical, commercial, or general knowledge in nature
- Could be found in a library or reputable publication

When in doubt, lean toward SAFE. Only block clear violations.
Provide a short, user-friendly reason either way.
"""

_input_guardrail_agent = Agent(
    name="InputGuardrailAgent",
    instructions=INPUT_GUARDRAIL_INSTRUCTIONS,
    model=os.environ.get("MODEL"),
    output_type=GuardrailDecision,
)


@input_guardrail
async def research_input_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """
    Runs before the OrchestratorAgent processes any query.
    Blocks harmful or off-topic research requests.
    """
    # Extract plain text from the input
    text = input if isinstance(input, str) else str(input)

    result = await Runner.run(
        _input_guardrail_agent,
        f"Research query to evaluate:\n{text}",
        context=ctx.context,
    )
    decision: GuardrailDecision = result.final_output_as(GuardrailDecision)

    return GuardrailFunctionOutput(
        output_info=decision,
        tripwire_triggered=not decision.is_safe,   # True = block the request
    )


# ── Output Guardrail ──────────────────────────────────────────────────────────

OUTPUT_GUARDRAIL_INSTRUCTIONS = """
You are a safety reviewer for a research report generation system.

Review the final research report and decide if it is SAFE to deliver to the user.

Mark as UNSAFE (is_safe=False) if the report:
- Contains step-by-step instructions for creating weapons, drugs, or malware
- Includes real personal/private information about private individuals
- Contains hate speech, discrimination, or targeted harassment
- Reproduces content that is clearly defamatory or legally problematic

Mark as SAFE (is_safe=True) if the report:
- Discusses sensitive topics at an informational/analytical level
- Contains opinions, analysis, or summaries of publicly available information
- Is factual, balanced, and references legitimate sources

Provide a short reason for your decision.
"""

_output_guardrail_agent = Agent(
    name="OutputGuardrailAgent",
    instructions=OUTPUT_GUARDRAIL_INSTRUCTIONS,
    model=os.environ.get("MODEL"),
    output_type=GuardrailDecision,
)


@output_guardrail
async def research_output_guardrail(
    ctx: RunContextWrapper,
    agent: Agent,
    output,                        # the agent's final output object
) -> GuardrailFunctionOutput:
    """
    Runs after the OrchestratorAgent finishes.
    Blocks reports that contain harmful or inappropriate content.
    """
    # Extract the text from the output (could be a string or structured object)
    report_text = output if isinstance(output, str) else str(output)

    result = await Runner.run(
        _output_guardrail_agent,
        f"Report to review:\n{report_text[:4000]}",  # truncate for speed
        context=ctx.context,
    )
    decision: GuardrailDecision = result.final_output_as(GuardrailDecision)

    return GuardrailFunctionOutput(
        output_info=decision,
        tripwire_triggered=not decision.is_safe,
    )