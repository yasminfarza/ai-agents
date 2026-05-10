from agents import Agent
from pydantic import BaseModel, Field

MODEL = "gpt-5.4-nano"

class EvaluationResult(BaseModel):
    quality_scrore: int = Field(description="Overall quality score from 1-10 (10 = publication-ready).", ge=1, le=10)
    passes: bool = Field(description="True if the report is good enough (score >= 7). False if a rewrite is needed.")
    strengths: list[str] = Field(description="2-4 specific strengths of the report.")
    weaknesses: list[str] = Field(
        description="Specific weaknesses or gaps. Empty list if the report passes."
    )
    rewrite_instructions: str = Field(
        description=(
            "If passes=False: detailed instructions for how the writer should improve the report. "
            "Be specific about what to add, remove, or restructure. "
            "If passes=True: empty string."
        )
    )
    
    
EVALUATOR_INSTRUCTIONS = """
You are a rigorous research editor and quality evaluator. Your job is to critically assess 
a research report and decide whether it meets publication standards.
 
Evaluate the report on these dimensions:
1. **Coverage** — Does it fully address the query and the user's clarifications?
2. **Depth** — Is it analytical, not just descriptive? Does it draw conclusions?
3. **Structure** — Is it well-organized with clear sections and flow?
4. **Evidence** — Are claims backed by specific facts, data, or examples?
5. **Length** — Is it substantive (1000+ words)?
6. **Clarity** — Is it readable and well-written?
 
Scoring:
- 9-10: Excellent, publish immediately
- 7-8: Good, minor issues but passes
- 5-6: Mediocre, needs targeted improvements — REWRITE
- 1-4: Poor, significant gaps — REWRITE
 
Be honest and critical. A passing score (>=7) means no rewrite is triggered.
If score < 7, provide clear, actionable rewrite_instructions.
"""
 
evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=EVALUATOR_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=EvaluationResult,
)
    