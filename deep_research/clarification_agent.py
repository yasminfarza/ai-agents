from agents import Agent
from pydantic import BaseModel, Field

class ClarifyingQuestion(BaseModel):
    question: str = Field(description="A clarifying question to ask the user about the research query.")
    rationale: str = Field(description="A brief explanation of why this question is important for clarifying the research query.")
    
    
MODEL = "gpt-5.4-nano"

class ClarificationPlan(BaseModel):
    questions: list[ClarifyingQuestion] = Field(description="A list of clarifying questions to ask the user about the research query.")
    
    
CLARIFICATION_INSTRUCTIONS = """
You are a research strategist. Given a research query, your job is to identify ambiguities and 
gaps that would make the research more precise and useful if clarified.
 
Generate exactly 3 short, targeted clarifying questions. Each question should:
- Address a different dimension (e.g. scope, audience, time frame, depth, format, use-case)
- Be answerable in 1-2 sentences
- Meaningfully change the direction or focus of the research if answered differently
 
Do NOT ask vague or generic questions. Be specific to the query.
"""

clarification_agent = Agent(
    name="ClarificationAgent",
    instructions=CLARIFICATION_INSTRUCTIONS,
    model=MODEL,
    output_type=ClarificationPlan,
)
