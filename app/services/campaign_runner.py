from datetime import datetime
from time import sleep
from app.data.database import get_db_connection
from app.config import DevelopmentConfig as Config
from bson.objectid import ObjectId

# Initialize MongoDB connection
_, db = get_db_connection(Config)


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
        user = db["users"].find_one({"_id": ObjectId(uid)})
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

        # Simulate sending with retry logic
        success = False
        for attempt in range(3):
            try:
                print(f"[Attempt {attempt+1}] Sending to {uid}: {rendered_text}")
                # In real setup, call Twilio API here
                success = True
                break
            except Exception:
                sleep(1)  # Retry after 1s if failed

        if success:
            log_entry.update({
                "decision": "SENT",
                "status": "SUCCESS"
            })
            total_sent += 1
        else:
            log_entry.update({
                "decision": "FAILED",
                "status": "ERROR",
                "reason": "Max retries reached"
            })

        # Store audit record
        db["delivery_receipts"].insert_one(log_entry)
        total_processed += 1

        # Enforce rate limit
        if total_processed % rate_limit == 0:
            print(f"Rate limit reached ({rate_limit} messages). Sleeping 60s...")
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
