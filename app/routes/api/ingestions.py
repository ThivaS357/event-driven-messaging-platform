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

    db["events_inbound"].insert_many(resolved)
    return jsonify({"message": "Events ingested", "count": len(resolved)}), 200
