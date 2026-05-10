import os
from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 1

class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
    
PLANNER_INSTRUCTIONS = f"""
You are a research planning expert. Given a research query AND a set of clarifying answers 
from the user, produce a precise set of {HOW_MANY_SEARCHES} web search queries.
 
The clarification answers are crucial — use them to:
- Narrow or broaden scope as indicated
- Target the right audience level (beginner vs expert)
- Focus on the right time period
- Prioritize the right subtopics
 
Each search query should be:
- Specific and search-engine-friendly (3-8 words)
- Distinct from the others (no redundancy)
- Directly motivated by the query + clarifications
 
Output exactly {HOW_MANY_SEARCHES} search items.
"""
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model=os.environ.get("MODEL", "gpt-5.4-nano"),
    output_type=WebSearchPlan,
)