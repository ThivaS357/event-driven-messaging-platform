from flask import Blueprint, request, jsonify, current_app
from app.data.database import get_db_connection, utc_now
from app.data.models.segment import SegmentModel
from pydantic import ValidationError
from datetime import datetime
from app.config import Config
from bson.objectid import ObjectId

segments_bp = Blueprint("segments_api", __name__, url_prefix="/segments")

@segments_bp.route("/", methods=["GET"])
def list_segments():
    """Lists all segments."""
    _, db = get_db_connection(Config)
    segments = list(db.segments.find({}))
    for segment in segments:
        segment["_id"] = str(segment["_id"])
    return jsonify(segments), 200

@segments_bp.route("/", methods=["POST"])
def create_segment():
    """Creates a new segment."""
    _, db = get_db_connection(Config)
    data = request.get_json()
    try:
        segment = SegmentModel(**data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    segment.created_at = utc_now()
    segment.updated_at = utc_now()
    
    db["segments"].insert_one(segment.model_dump(by_alias=True))
    return jsonify({"message": "Segment created successfully"}), 201

@segments_bp.route("/<string:segment_id>", methods=["PUT"])
def update_segment(segment_id):
    """Updates an existing segment by its ID."""
    _, db = get_db_connection(Config)
    existing = db["segments"].find_one({"_id": ObjectId(segment_id)})
    if not existing:
        return jsonify({"error": "Segment not found"}), 404
    
    existing.pop('_id', None)
    
    data = request.get_json()
    merged = {**existing, **data, "updated_at": datetime.utcnow()}
    
    try:
        segment = SegmentModel(**merged)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    db["segments"].update_one({"_id": ObjectId(segment_id)}, {"$set": segment.model_dump(by_alias=True)})
    return jsonify({"message": "Segment updated successfully"}), 200

@segments_bp.route("/<string:segment_id>", methods=["DELETE"])
def delete_segment(segment_id):
    """Deletes a segment by its ID."""
    _, db = get_db_connection(Config)
    res = db["segments"].delete_one({"_id": ObjectId(segment_id)})
    if res.deleted_count == 0:
        return jsonify({"error": "Segment not found"}), 404
    return jsonify({"message": "Segment deleted successfully"}), 200