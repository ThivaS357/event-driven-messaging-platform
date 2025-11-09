import io, csv, json
from flask import Blueprint, request, jsonify
from app.data.models.user import UserModel
from app.data.database import get_db_connection
from app.config import DevelopmentConfig as Config
from datetime import datetime
from pydantic import ValidationError

ingestion_bp = Blueprint("ingestion_api", __name__, url_prefix="/ingestions")
_, db = get_db_connection(Config)

@ingestion_bp.route("/users", methods=["POST"])
def ingest_users():
    """
    Upload a CSV or JSON user file for ingestion.
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    filename = file.filename.lower()
    if filename.endswith(".csv"):
        records = list(csv.DictReader(io.StringIO(file.stream.read().decode("utf-8"))))
    elif filename.endswith(".json"):
        records = json.load(file.stream)
    else:
        return jsonify({"error": "Unsupported file format"}), 400

    summary = {
        "total": len(records),
        "valid": 0,
        "invalid": 0,
        "duplicates": 0,
        "merged": 0,
        "new": 0
    }

    for record in records:
        try:
            user = UserModel(**record)
        except ValidationError:
            summary["invalid"] += 1
            continue

        existing = db["users"].find_one({"_id": user.id})
        if existing:
            merged = {**existing, **user.model_dump(by_alias=True), "updated_at": datetime.utcnow()}
            db["users"].update_one({"_id": user.id}, {"$set": merged})
            summary["merged"] += 1
        else:
            db["users"].insert_one(user.model_dump(by_alias=True))
            summary["new"] += 1
        summary["valid"] += 1

    return jsonify({"message": "Ingestion completed", "summary": summary}), 200


@ingestion_bp.route("/events", methods=["POST"])
def ingest_jsonl_events():
    """
    Ingest a JSONL trigger events file and resolve segment recipients.
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    events = []
    for line in file.stream:
        try:
            event = json.loads(line.decode("utf-8").strip())
            events.append(event)
        except json.JSONDecodeError:
            continue

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

