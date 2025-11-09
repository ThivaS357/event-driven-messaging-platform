import io, csv, json
from flask import Blueprint, request, jsonify
from app.data.models.user import UserModel
from app.data.database import get_db_connection
from app.config import DevelopmentConfig as Config
from datetime import datetime
from pydantic import ValidationError

ingestion_bp = Blueprint("ingestion_api", __name__, url_prefix="/ingestions")

@ingestion_bp.route("/users", methods=["POST"])
def ingest_users():
    """
    Upload a CSV or JSON user file for ingestion.
    """
    _, db = get_db_connection(Config)
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    # Determine file type and parse records
    filename = file.filename.lower()
    if filename.endswith(".csv"):
        records = list(csv.DictReader(io.StringIO(file.stream.read().decode("utf-8"))))
    elif filename.endswith(".json"):
        records = json.load(file.stream)
    else:
        return jsonify({"error": "Unsupported file format"}), 400

    # Initialize a summary of the ingestion process
    summary = {
        "total": len(records),
        "valid": 0,
        "invalid": 0,
        "duplicates": 0,
        "merged": 0,
        "new": 0
    }

    for record in records:
        # Clean and validate each record using the Pydantic model
        try:
            cleaned_record = {str(k).strip().lstrip("\ufeff"): v for k, v in record.items()}
            
            if "attributes" in cleaned_record and isinstance(cleaned_record["attributes"], str):
                try:
                    cleaned_record["attributes"] = json.loads(cleaned_record["attributes"])
                except json.JSONDecodeError:
                    cleaned_record["attributes"] = {}
            
            user = UserModel(**cleaned_record)
        except ValidationError as e:
            print("❌ Validation failed for record:", cleaned_record)
            print("📋 Details:", e.errors())
            summary["invalid"] += 1
            continue

        # Check for existing user and merge/update or create new
        existing = db["users"].find_one({"$or":[{"id": user.id}, {"_id": user.id}]})
        if existing:
            existing.pop('_id', None)
            new_user_data = user.model_dump(by_alias=True, exclude={"_id","id"})
            merged = {**existing, **new_user_data, "updated_at": datetime.utcnow()}
            db["users"].update_one({"id": user.id}, {"$set": merged})
            summary["merged"] += 1
        else:
            db["users"].insert_one(user.dict())
            summary["new"] += 1
        summary["valid"] += 1

    return jsonify({"message": "Ingestion completed", "summary": summary}), 200


@ingestion_bp.route("/events", methods=["POST"])
def ingest_jsonl_events():
    """
    Ingest a JSONL trigger events file and resolve segment recipients.
    """
    _, db = get_db_connection(Config)
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    # Read each line of the JSONL file as a separate JSON object
    events = []
    for line in file.stream:
        try:
            event = json.loads(line.decode("utf-8").strip())
            events.append(event)
        except json.JSONDecodeError:
            continue

    # Resolve recipients for each event based on segment rules
    resolved = []
    triggered = 0
    for ev in events:
        rule = ev.get("segment_rule", {})
        topic = rule.get("topic")
        if not topic:
            continue

        # Find users subscribed to the topic
        user_ids = [
            sub["user_id"]
            for sub in db["subscriptions"].find({"topic": topic})
        ]

        ev["recipients"] = user_ids
        resolved.append(ev)
        
        # If a scheduled campaign exists for the topic, trigger it
        campaign = db["campaigns"].find_one({"topic": topic, "status": "scheduled"})
        if campaign:
            from app.services.campaign_runner import run_campaign
            run_campaign(campaign["_id"])
            triggered += 1
            
    if resolved:
        db["events_inbound"].insert_many(resolved)

    return jsonify({"message": "Events ingested", "count": len(resolved), "campaigns_triggered": triggered}), 200


@ingestion_bp.route("/stats", methods=["GET"])
def get_campaign_stats():
    """
    Returns delivery and user statistics for dashboard display.
    """
    _, db = get_db_connection(Config)
    total_users = db["users"].count_documents({})
    opt_outs = db["users"].count_documents({"consent_state": "STOPPED"})
    total_receipts = db["delivery_receipts"].count_documents({})
    sent = db["delivery_receipts"].count_documents({"status": "SUCCESS"})
    failed = db["delivery_receipts"].count_documents({"status": "ERROR"})

    delivery_pct = (sent / total_receipts * 100) if total_receipts > 0 else 0
    failed_pct = (failed / total_receipts * 100) if total_receipts > 0 else 0

    return jsonify({
        "total_users": total_users,
        "opt_outs": opt_outs,
        "sent": sent,
        "failed": failed,
        "delivery_pct": round(delivery_pct, 2),
        "failed_pct": round(failed_pct, 2)
    }), 200
