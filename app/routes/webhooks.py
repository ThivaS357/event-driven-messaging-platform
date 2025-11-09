from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from app.data.database import get_db_connection
from app.config import Config
import re

webhook_bp = Blueprint('webhooks', __name__, url_prefix='/twilio')

@webhook_bp.route('/inbound', methods=['POST'])
def inbound_message():
    """
    Twilio inbound WhatsApp message webhook.
    Handles START, STOP, SUBSCRIBE, and UNSUBSCRIBE commands.
    """
    _, db = get_db_connection(Config)
    data = request.form.to_dict()
    from_number = data.get("From", "").replace("whatsapp:", "")
    body = data.get("Body", "").strip().upper()
    
    
    normalized = {"command": None, "topic": None}
    
    if body == "START":
        db["users"].update_one({"id": from_number}, {"$set": {"consent_state": "SUBSCRIBED"}}, upsert=True)
        normalized["command"] = "START"
    elif body == "STOP":
        db["users"].update_one({"id": from_number}, {"$set": {"consent_state": "STOPPED"}}, upsert=True)
        normalized["command"] = "STOP"
    elif body.startswith("SUBSCRIBE "):
        topic = body.split("SUBSCRIBE ", 1)[1]
        normalized.update({"command": "SUBSCRIBE", "topic": topic})
        db["subscriptions"].update_one(
            {"user_id": from_number, "topic": topic},
            {"$set": {"user_id": from_number, "topic": topic, "subscribed_at": datetime.utcnow()}},
            upsert=True
        )
    elif body.startswith("UNSUBSCRIBE "):
        topic = body.split("UNSUBSCRIBE ", 1)[1]
        normalized.update({"command": "UNSUBSCRIBE", "topic": topic})
        db["subscriptions"].delete_one({"user_id": from_number, "topic": topic})

    record = {
        "from": from_number,
        "body": data.get("Body", ""),
        "timestamp": datetime.utcnow(),
        "type": "inbound",
        **normalized
    }
    
    db["events_inbound"].insert_one(record)

    return jsonify({"status": "processed", "command": normalized["command"], "topic": normalized.get("topic")}), 200

@webhook_bp.route('/status', methods=['POST'])
def message_status_callback():
    """
    Twilio status callback webhook for outbound message lifecycle.
    Tracks queued, sending, sent, delivered, read, failed, etc.
    """
    _, db = get_db_connection(current_app.config)
    data = request.form.to_dict()
    message_sid = data.get("MessageSid")
    message_status = data.get("MessageStatus")
    error_code = data.get("ErrorCode")

    record = {
        "message_sid": message_sid,
        "status": message_status,
        "error_code": error_code,
        "timestamp": datetime.utcnow(),
        "type": "status_callback"
    }

    db["delivery_receipts"].update_one(
        {"message_sid": message_sid},
        {"$set": record},
        upsert=True
    )

    return jsonify({"status": "updated"}), 200