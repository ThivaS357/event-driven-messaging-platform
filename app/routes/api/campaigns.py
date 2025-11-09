from flask import Blueprint, request, jsonify
from app.data.database import get_db_connection, utc_now
from app.data.models.compaign import CompaignModel
from app.config import Config
from pydantic import ValidationError
from datetime import datetime

campaigns_bp = Blueprint("campaigns_api", __name__, url_prefix="/campaigns")

_, db = get_db_connection(Config)

@campaigns_bp.route("/", methods=["GET"])
def list_campaigns():
    campaigns = list(db.campaigns.find({}))
    for campaign in campaigns:
        campaign["_id"] = str(campaign["_id"])
    return jsonify(campaigns), 200


@campaigns_bp.route("/", methods=["POST"])
def create_campaign():
    data = request.get_json()
    try:
        campaign = CompaignModel(**data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    campaign.created_at = utc_now()
    campaign.updated_at = utc_now()
    

    db["campaigns"].insert_one(campaign.dict())
    return jsonify({"message": "Campaign created successfully"}), 201


@campaigns_bp.route("/<string:camp_id>", methods=["PUT"])
def update_campaign(camp_id):
    
    existing = db["campaigns"].find_one({"_id": camp_id})
    if not existing:
        return jsonify({"error": "Campaign not found"}), 404
    
    data = request.get_json()
    merged = {**existing, **data}
    merged["updated_at"] = datetime.utcnow()
    
    try:
        campaign = CompaignModel(**merged)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    db["campaigns"].update_one({"_id": camp_id}, {"$set": campaign.model_dump(by_alias=True)})
    return jsonify({"message": "Campaign updated successfully"}), 200


@campaigns_bp.route("/<string:camp_id>", methods=["DELETE"])
def delete_campaign(camp_id):
    res = db["campaigns"].delete_one({"_id": camp_id})
    if res.deleted_count == 0:
        return jsonify({"error": "Campaign not found"}), 404
    return jsonify({"message": "Campaign deleted successfully"}), 200
