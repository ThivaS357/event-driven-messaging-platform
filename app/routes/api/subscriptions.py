from flask import Blueprint, request, jsonify
from app.data.database import get_db_connection, utc_now
from app.data.models.subscription import SubscriptionModel
from app.config import Config
from pydantic import ValidationError
from datetime import datetime

subscriptions_bp = Blueprint("subscriptions_api", __name__, url_prefix="/subscriptions")

@subscriptions_bp.route("/", methods=["GET"])
def list_subscriptions():
    _, db = get_db_connection(Config)
    
    subs = list(db.subscriptions.find({}))
    for sub in subs:
        sub["_id"] = str(sub["_id"])
    return jsonify(subs), 200


@subscriptions_bp.route("/", methods=["POST"])
def create_subscription():
    
    _, db = get_db_connection(Config)
    
    data = request.get_json()
    try:
        sub = SubscriptionModel(**data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    db["subscriptions"].insert_one(sub.dict())
    return jsonify({"message": "Subscription created successfully"}), 201


@subscriptions_bp.route("/<string:sub_id>", methods=["PUT"])
def update_subscription(sub_id):
    
    _, db = get_db_connection(Config)
    
    existing = db["subscriptions"].find_one({"_id": sub_id})
    if not existing:
        return jsonify({"error": "Subscription not found"}), 404

    data = request.get_json()
    merged = {**existing, **data}   
    merged["updated_at"] = datetime.utcnow()
    
    try:
        sub = SubscriptionModel(**merged)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    db["subscriptions"].update_one({"_id": sub_id}, {"$set": sub})
    
    return jsonify({"message": "Subscription updated successfully"}), 200


@subscriptions_bp.route("/<string:sub_id>", methods=["DELETE"])
def delete_subscription(sub_id):
    
    _, db = get_db_connection(Config)
    
    res = db["subscriptions"].delete_one({"_id": sub_id})
    if res.deleted_count == 0:
        return jsonify({"error": "Subscription not found"}), 404
    return jsonify({"message": "Subscription deleted successfully"}), 200
