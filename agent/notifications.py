import sys
sys.path.append("C:\\Users\\KIIT0001\\inventory-agent")

import os
import json
import smtplib
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")

def send_slack(message: str):
    if not SLACK_WEBHOOK or SLACK_WEBHOOK == "your_key_here":
        print(" Slack webhook not configured")
        return False
    try:
        data = json.dumps({"text": message, "username": "Inventory Agent"}).encode()
        req  = urllib.request.Request(
            SLACK_WEBHOOK, data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=8)
        return True
    except Exception as e:
        print(f" Slack failed: {e}")
        return False

def send_email(subject: str, body: str):
    smtp_server   = os.getenv("BREVO_SMTP_SERVER", "smtp-relay.brevo.com")
    smtp_port     = int(os.getenv("BREVO_SMTP_PORT", 587))
    smtp_login    = os.getenv("BREVO_SMTP_LOGIN", "")
    smtp_password = os.getenv("BREVO_SMTP_PASSWORD", "")
    from_email    = os.getenv("EMAIL_ADDRESS", "")

    if not smtp_login or smtp_login == "your_key_here":
        print(" Email not configured")
        return False

    try:
        msg = MIMEMultipart()
        msg['From']    = from_email
        msg['To']      = from_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_login, smtp_password)
            server.send_message(msg)

        print(f"Email sent to {from_email}")
        return True
    except Exception as e:
        print(f" Email failed: {e}")
        return False

def build_notification(state: dict, escalated: bool = False) -> str:
    decision = state.get("decision", {})
    forecast = state.get("forecast", {})
    status   = " NEEDS APPROVAL" if escalated else " AUTO-ORDERED"
    urgency  = decision.get("urgency", "NORMAL")

    urgency_emoji = "🔴" if urgency == "CRITICAL" else "🟡" if urgency == "WARNING" else "🟢"

    msg = f"""
{status} {urgency_emoji} {urgency}

 *Product:* {state.get('product_name')} (ID: {state.get('product_id')})
 *Current stock:* {state.get('current_stock')} units
 *Stockout in:* {state.get('doi')} days
 *Forecast (7d):* {forecast.get('ensemble', 0)} units ({forecast.get('confidence_pct', 0)}% confidence)

 *Reorder qty:* {decision.get('recommended_qty', 0)} units
 *Supplier:* {decision.get('selected_supplier', 'Unknown')}
 *Reason:* {decision.get('reason', 'N/A')}
 *PO Reference:* {state.get('po_reference', 'PENDING')}
 *Agent confidence:* {int(state.get('confidence', 0) * 100)}%
 *Time:* {datetime.now().strftime('%d %b %Y %H:%M')}
""".strip()
    return msg

def notify_auto_order(state: dict):
    msg      = build_notification(state, escalated=False)
    decision = state.get("decision", {})

    print(f"\n Sending notifications...")
    send_slack(msg)
    send_email(
        subject=f"[AUTO-ORDERED] {state.get('product_name')} — {decision.get('recommended_qty')} units",
        body=msg
    )
    return True

def notify_escalation(state: dict):
    msg      = build_notification(state, escalated=True)
    decision = state.get("decision", {})

    print(f"\n Sending escalation notifications...")
    send_slack(msg)
    send_email(
        subject=f"[NEEDS APPROVAL] {state.get('product_name')} — action required",
        body=msg
    )
    return True