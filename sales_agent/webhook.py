"""
webhook.py
----------------
Flask webhook server that receives email replies from SendGrid Inbound Parse
and automatically responds using an AI SDR Responder Agent.

How it works:
    1. Prospect replies to your cold email
    2. SendGrid forwards the reply to POST /reply (this server)
    3. SDR Responder Agent reads the reply and sends a warm response

Setup:
    1. pip install flask sendgrid openai-agents python-dotenv
    2. Set environment variables in .env file
    3. Run: python webhook.py
    4. Expose locally with: ngrok http 5000
    5. Set the ngrok URL in SendGrid → Settings → Inbound Parse
"""

import asyncio
import os
from typing import Dict

import sendgrid
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from agents import Agent, Runner, trace, function_tool
from sendgrid.helpers.mail import Mail, Email, To, Content

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(override=True)

app = Flask(__name__)
MODEL = "gpt-5.4-nano"


# ---------------------------------------------------------------------------
# Email Reply Tool (SendGrid)
# ---------------------------------------------------------------------------

@function_tool
def send_reply_email(to: str, subject: str, body: str) -> Dict[str, str]:
    """Send a reply email to a prospect who responded to our cold email."""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(os.environ.get("SENDGRID_FROM_EMAIL"))
    to_email = To(to)
    content = Content("text/plain", body)
    mail = Mail(from_email, to_email, subject, content).get()
    sg.client.mail.send.post(request_body=mail)
    return {"status": "success", "sent_to": to}


# ---------------------------------------------------------------------------
# SDR Responder Agent
# ---------------------------------------------------------------------------

def create_sdr_responder() -> Agent:
    """Create the SDR Responder agent that replies to prospect emails."""
    return Agent(
        name="SDR Responder",
        instructions=(
            "You are a friendly and professional Sales Development Representative at ComplAI. "
            "A prospect has replied to your cold email. Your job is to: "
            "(1) Respond warmly and acknowledge their reply. "
            "(2) Address any questions or concerns they raised. "
            "(3) Try to schedule a product demo. "
            "Use the send_reply_email tool to send your response."
        ),
        tools=[send_reply_email],
        model=MODEL,
    )


# ---------------------------------------------------------------------------
# Core Response Function
# ---------------------------------------------------------------------------

async def sdr_agent_respond(sender: str, subject: str, body: str) -> None:
    """Run the SDR Responder agent to reply to a prospect's email."""
    agent = create_sdr_responder()

    message = (
        f"A prospect replied to our cold email.\n"
        f"Their email address: {sender}\n"
        f"Subject: {subject}\n"
        f"Their message:\n{body}\n\n"
        f"Please write a warm, helpful reply and send it using send_reply_email."
    )

    with trace("SDR Auto-Reply"):
        await Runner.run(agent, message)


# ---------------------------------------------------------------------------
# Flask Webhook Route
# ---------------------------------------------------------------------------

@app.route("/reply", methods=["POST"])
def handle_reply():
    """
    Webhook endpoint for SendGrid Inbound Parse.
    SendGrid POSTs incoming emails here as form data.
    """
    sender  = request.form.get("from", "")
    subject = request.form.get("subject", "Re: Your Inquiry")
    body    = request.form.get("text", "")

    print(f"\n📬 Incoming reply from: {sender}")
    print(f"📌 Subject: {subject}")
    print(f"📝 Body preview: {body[:100]}...")

    if not sender or not body:
        return jsonify({"error": "Missing sender or body"}), 400

    # Run the async agent in the sync Flask context
    asyncio.run(sdr_agent_respond(sender, subject, body))

    print(f"✅ Auto-reply sent to {sender}")
    return jsonify({"status": "success"}), 200


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check to confirm the server is running."""
    return jsonify({"status": "running"}), 200


# ---------------------------------------------------------------------------
# Run Server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🚀 SDR Reply Webhook Server starting...")
    print("📡 Listening on http://localhost:5000")
    print("🔗 Webhook endpoint: POST /reply")
    app.run(host="0.0.0.0", port=5000, debug=True)