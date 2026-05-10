import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool

import ssl
import certifi

ssl._create_default_https_context = ssl.create_default_context
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

MODEL = "gpt-5.4-nano"

@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    sg.client.session.verify = certifi.where()
    from_email = Email(os.environ.get("SENDGRID_FROM_EMAIL"))
    to_email = To(os.environ.get("SENDGRID_TO_EMAIL"))
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return "success"

EMAIL_INSTRUCTIONS = """
You are able to send a nicely formatted HTML email based on a detailed research report.
 
You will be provided with a Markdown report. Convert it into clean, well-presented HTML:
- Use proper HTML headings (h1, h2, h3)
- Use styled paragraphs and lists
- Add a professional header banner
- Include the follow-up questions section at the end
- Choose a clear, descriptive subject line
 
Then send exactly one email using your tool.
"""

email_agent = Agent(
    name="Email agent",
    instructions=EMAIL_INSTRUCTIONS,
    tools=[send_email],
    model=MODEL,
)
    