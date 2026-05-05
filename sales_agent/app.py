"""
sdr_agent.py
------------
Automated Sales Development Representative (SDR) Agent System.
Uses OpenAI Agents SDK to generate, evaluate, and send cold sales emails via SendGrid.

Architecture:
    Sales Manager Agent
    ├── tool1 → sales_agent1 (Professional)
    ├── tool2 → sales_agent2 (Engaging/Witty)
    ├── tool3 → sales_agent3 (Concise)
    └── handoff → Email Manager Agent
                  ├── subject_writer tool
                  ├── html_converter tool
                  └── send_html_email tool → SendGrid → 📧
"""

import asyncio
import os
from typing import Dict

import sendgrid
from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
from sendgrid.helpers.mail import Mail, Email, To, Content

import ssl
import certifi


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(override=True)

ssl._create_default_https_context = ssl.create_default_context
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

COMPANY_NAME = "ComplAI"
COMPANY_DESC = (
    "a company that provides a SaaS tool for ensuring SOC2 compliance "
    "and preparing for audits, powered by AI"
)
MODEL = "gpt-5.4-nano"


# ---------------------------------------------------------------------------
# Email Tool (SendGrid)
# ---------------------------------------------------------------------------

@function_tool
def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an HTML email to all sales prospects via SendGrid."""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    sg.client.session.verify = certifi.where()
    from_email = Email(os.environ.get("SENDGRID_FROM_EMAIL"))
    to_email = To(os.environ.get("SENDGRID_TO_EMAIL"))
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    sg.client.mail.send.post(request_body=mail)
    return {"status": "success"}


# ---------------------------------------------------------------------------
# Sales Writer Agents
# ---------------------------------------------------------------------------

def create_sales_agents() -> tuple[Agent, Agent, Agent]:
    """Create three sales writer agents with different styles."""

    professional = Agent(
        name="Professional Sales Agent",
        instructions=(
            f"You are a sales agent working for {COMPANY_NAME}, {COMPANY_DESC}. "
            "You write professional, serious cold emails."
        ),
        model=MODEL,
    )

    engaging = Agent(
        name="Engaging Sales Agent",
        instructions=(
            f"You are a humorous, engaging sales agent working for {COMPANY_NAME}, {COMPANY_DESC}. "
            "You write witty, engaging cold emails that are likely to get a response."
        ),
        model=MODEL,
    )

    concise = Agent(
        name="Busy Sales Agent",
        instructions=(
            f"You are a busy sales agent working for {COMPANY_NAME}, {COMPANY_DESC}. "
            "You write concise, to the point cold emails."
        ),
        model=MODEL,
    )

    return professional, engaging, concise


# ---------------------------------------------------------------------------
# Email Formatter Agent (with Handoff)
# ---------------------------------------------------------------------------

def create_emailer_agent() -> Agent:
    """Create the Email Manager agent that formats and sends emails."""

    subject_writer = Agent(
        name="Email Subject Writer",
        instructions=(
            "You write compelling subjects for cold sales emails. "
            "Given an email body, write a subject line likely to get a response."
        ),
        model=MODEL,
    )

    html_converter = Agent(
        name="HTML Email Body Converter",
        instructions=(
            "You convert plain-text or markdown email bodies into clean HTML emails "
            "with a simple, clear, and compelling layout and design."
        ),
        model=MODEL,
    )

    subject_tool = subject_writer.as_tool(
        tool_name="subject_writer",
        tool_description="Write a subject for a cold sales email",
    )
    html_tool = html_converter.as_tool(
        tool_name="html_converter",
        tool_description="Convert a text email body to an HTML email body",
    )

    return Agent(
        name="Email Manager",
        instructions=(
            "You are an email formatter and sender. You receive the body of an email. "
            "Steps: (1) Use subject_writer to write a subject. "
            "(2) Use html_converter to convert the body to HTML. "
            "(3) Use send_html_email to send the final email."
        ),
        tools=[subject_tool, html_tool, send_html_email],
        model=MODEL,
        handoff_description="Format an email as HTML and send it via SendGrid",
    )


# ---------------------------------------------------------------------------
# Sales Manager Agent (Orchestrator)
# ---------------------------------------------------------------------------

def create_sales_manager(
    sales_agents: tuple[Agent, Agent, Agent],
    emailer_agent: Agent,
) -> Agent:
    """Create the Sales Manager agent that orchestrates the full workflow."""

    agent1, agent2, agent3 = sales_agents

    draft_tools = [
        agent1.as_tool(tool_name="sales_agent1", tool_description="Write a cold sales email"),
        agent2.as_tool(tool_name="sales_agent2", tool_description="Write a cold sales email"),
        agent3.as_tool(tool_name="sales_agent3", tool_description="Write a cold sales email"),
    ]

    instructions = """
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email.

Steps:
1. Generate Drafts: Use ALL THREE sales_agent tools to generate three different email drafts.
   Do not proceed until all three drafts are ready.

2. Evaluate and Select: Review the drafts and choose the single best one.
   You may regenerate drafts if unsatisfied with the results.

3. Handoff: Pass ONLY the winning email draft to the 'Email Manager' agent.
   The Email Manager will handle formatting and sending.

Rules:
- Never write email drafts yourself — always use the sales_agent tools.
- Hand off exactly ONE email to the Email Manager — never more than one.
"""

    return Agent(
        name="Sales Manager",
        instructions=instructions,
        tools=draft_tools,
        handoffs=[emailer_agent],
        model=MODEL,
    )


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

async def run_sdr(message: str) -> None:
    """Run the full SDR agent pipeline for a given message."""
    sales_agents = create_sales_agents()
    emailer_agent = create_emailer_agent()
    sales_manager = create_sales_manager(sales_agents, emailer_agent)

    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)

    print("✅ SDR pipeline complete.")
    print(f"Final output:\n{result.final_output}")


if __name__ == "__main__":
    message = "Send out a cold sales email addressed to Dear CEO from Alice"
    asyncio.run(run_sdr(message))