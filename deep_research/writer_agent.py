from pydantic import BaseModel, Field
from agents import Agent

MODEL = "gpt-5.4-nano"


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")
    
    quality_score_self: int = Field(
        description="Self-assessed quality score from 1-10 for this report (10 = excellent).",
        ge=1,
        le=10,
    )
    
    
WRITER_INSTRUCTIONS = """
You are a senior researcher tasked with writing a cohesive, detailed report for a research query.
 
You will be provided with:
- The original query
- The user's clarification answers (use these to calibrate depth, tone, and focus)
- Summarized search results from a research assistant
 
Process:
1. First create a mental outline: structure, sections, flow
2. Write the full report in well-structured Markdown
3. Aim for 5-10 pages of content, at least 1000 words
4. Use headers, subheaders, bullet points, and tables where appropriate
5. Be analytical — don't just summarize, synthesize and draw conclusions
6. Cite specific facts and data points from the search results
 
The report must be genuinely useful to someone making decisions based on it.
"""


writer_agent = Agent(
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model=MODEL,
    output_type=ReportData,
)