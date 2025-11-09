from flask import Blueprint, request, jsonify, current_app
from app.data.database import get_db_connection, utc_now
from app.data.models.template import TemplateModel
from pydantic import ValidationError
from datetime import datetime

templates_bp = Blueprint("templates_api", __name__, url_prefix="/templates")

@templates_bp.route("/", methods=["GET"])
def list_templates():
    _, db = get_db_connection(current_app.config)
    templates = list(db.templates.find({}))
    for template in templates:
        template["_id"] = str(template["_id"])
    return jsonify(templates), 200

@templates_bp.route("/", methods=["POST"])
def create_template():
    _, db = get_db_connection(current_app.config)
    data = request.get_json()
    try:
        template = TemplateModel(**data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    template.created_at = utc_now()
    template.updated_at = utc_now()
    
    db["templates"].insert_one(template.model_dump(by_alias=True))
    return jsonify({"message": "Template created successfully"}), 201

@templates_bp.route("/<string:template_id>", methods=["PUT"])
def update_template(template_id):
    _, db = get_db_connection(current_app.config)
    existing = db["templates"].find_one({"_id": template_id})
    if not existing:
        return jsonify({"error": "Template not found"}), 404
    
    data = request.get_json()
    merged = {**existing, **data, "updated_at": datetime.utcnow()}
    
    try:
        template = TemplateModel(**merged)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    db["templates"].update_one({"_id": template_id}, {"$set": template.model_dump(by_alias=True)})
    return jsonify({"message": "Template updated successfully"}), 200

@templates_bp.route("/<string:template_id>", methods=["DELETE"])
def delete_template(template_id):
    _, db = get_db_connection(current_app.config)
    res = db["templates"].delete_one({"_id": template_id})
    if res.deleted_count == 0:
        return jsonify({"error": "Template not found"}), 404
    return jsonify({"message": "Template deleted successfully"}), 200