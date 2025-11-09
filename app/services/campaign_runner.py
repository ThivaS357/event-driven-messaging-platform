import os
import json
from datetime import datetime
from time import sleep
from bson.objectid import ObjectId
from twilio.rest import Client
from dotenv import load_dotenv
from app.data.database import get_db_connection
from app.config import DevelopmentConfig as Config

# Load .env environment variables
load_dotenv()

# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM")
TWILIO_CONTENT_SID = os.getenv("TWILIO_CONTENT_SID")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def is_quiet_hours(quiet_hours: dict) -> bool:
    """
    Checks if current time falls within defined quiet hours.
    Handles cases that wrap past midnight.
    """
    now = datetime.now().time()
    start = datetime.strptime(quiet_hours["start"], "%H:%M").time()
    end = datetime.strptime(quiet_hours["end"], "%H:%M").time()

    # Quiet period may wrap midnight (e.g., 22:00–06:00)
    if start < end:
        return start <= now <= end
    return now >= start or now <= end


def render_template(template: str, context: dict) -> str:
    """
    Performs basic variable replacement in a template string.
    Example: "Hello {{name}}" + {"name": "Thiva"} -> "Hello Thiva"
    """
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template


def run_campaign(campaign_id: str, rate_limit: int = 50):
    """
    Executes a campaign:
    - Fetches campaign, template, and users subscribed to the topic
    - Enforces consent and quiet hours
    - Sends WhatsApp messages via Twilio
    - Logs each delivery attempt in delivery_receipts
    """
    # Get DB connection inside the function to allow for mocking in tests
    _, db = get_db_connection(Config)

    # Fetch campaign
    campaign = db["campaigns"].find_one({"_id": ObjectId(campaign_id)})
    if not campaign:
        return {"error": f"Campaign '{campaign_id}' not found."}

    # Fetch associated template
    template = db["templates"].find_one({"_id": ObjectId(campaign["template_id"])})
    if not template:
        return {"error": "Template not found for this campaign."}

    topic = campaign.get("topic")
    quiet_hours = campaign.get("quiet_hours", {"start": "22:00", "end": "06:00"})

    # Get target users from subscriptions
    subs_cursor = db["subscriptions"].find({"topic": topic})
    user_ids = [sub["user_id"] for sub in subs_cursor]

    total_processed = 0
    total_sent = 0

    for uid in user_ids:
        user = db["users"].find_one({"id": uid})
        if not user:
            continue

        log_entry = {
            "campaign_id": campaign_id,
            "user_id": uid,
            "timestamp": datetime.utcnow(),
            "decision": None,
            "reason": None,
            "status": None
        }

        # Enforce consent (STOP)
        if user.get("consent_state") == "STOPPED":
            log_entry.update({
                "decision": "SKIPPED",
                "reason": "User opted out"
            })
            db["delivery_receipts"].insert_one(log_entry)
            continue

        # Enforce quiet hours
        if is_quiet_hours(quiet_hours):
            log_entry.update({
                "decision": "DELAYED",
                "reason": "Quiet hours"
            })
            db["delivery_receipts"].insert_one(log_entry)
            continue

        # Render message
        attributes = user.get("attributes", {})
        rendered_text = render_template(template["content"], attributes)

        # Prepare recipient
        recipient_number = user.get("id")
        if not recipient_number:
            log_entry.update({
                "decision": "FAILED",
                "status": "ERROR",
                "reason": "Missing phone number"
            })
            db["delivery_receipts"].insert_one(log_entry)
            continue

        if not str(recipient_number).startswith("whatsapp:"):
            recipient = f"whatsapp:{recipient_number}"
        else:
            recipient = recipient_number

        # Send via Twilio with retry logic
        success = False
        sid = None

        for attempt in range(3):
            try:
                print(f"[Attempt {attempt+1}] Sending WhatsApp message to {recipient}...")

                message = client.messages.create(
                    from_=TWILIO_WHATSAPP_FROM,
                    content_sid=TWILIO_CONTENT_SID,
                    content_variables=json.dumps({"1": rendered_text}),
                    to=recipient
                )

                sid = message.sid
                success = True
                print(f"Message sent to {recipient} | SID: {sid}")
                break

            except Exception as e:
                print(f"Error sending to {recipient}: {e}")
                sleep(2)

        # Update log entry
        if success:
            log_entry.update({
                "decision": "SENT",
                "status": "SUCCESS",
                "twilio_sid": sid
            })
            total_sent += 1
        else:
            log_entry.update({
                "decision": "FAILED",
                "status": "ERROR",
                "reason": "Max retries reached"
            })

        # Store delivery record
        db["delivery_receipts"].insert_one(log_entry)
        total_processed += 1

        # Enforce rate limit
        if total_processed % rate_limit == 0:
            print(f"Rate limit reached ({rate_limit}). Sleeping 60s...")
            sleep(60)

    # Finalize campaign
    db["campaigns"].update_one(
        {"_id": ObjectId(campaign_id)},
        {"$set": {"status": "completed", "last_run": datetime.utcnow()}}
    )

    print(f"Campaign '{campaign_id}' completed: {total_sent}/{total_processed} sent.")
    return {
        "message": f"Campaign '{campaign_id}' run completed.",
        "total_processed": total_processed,
        "total_sent": total_sent
    }
