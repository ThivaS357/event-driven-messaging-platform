from flask import Blueprint, request, jsonify
from flask import Blueprint, request, jsonify, current_app
from app.data.database import get_db_connection, utc_now
from app.data.models.user import UserModel
from app.config import Config
from pydantic import ValidationError
from datetime import datetime


users_bp = Blueprint('users_api', __name__, url_prefix='/users')


@users_bp.route('/', methods=['GET'])
def list_users():
    _, db = get_db_connection(Config)
    users = list(db.users.find({}))
    
    for user in users:
        user['_id'] = str(user['_id'])
    return jsonify(users), 200

@users_bp.route('/', methods=['POST'])
def create_user():
    _, db = get_db_connection(Config)
    data = request.get_json()
    try:
        user = UserModel(**data)
    except ValidationError as e:
        return jsonify(e.errors()), 400
    
    user.created_at = utc_now()
    user.updated_at = utc_now()
    
    db["users"].insert_one(user.dict())
    return jsonify({"message": "User created successfully"}), 201

@users_bp.route("/<string:user_id>", methods=["PUT"])
def update_user(user_id):
    _, db = get_db_connection(Config)
    # Get existing record
    existing = db["users"].find_one({"id": user_id})
    if not existing:
        return jsonify({"error": "User not found"}), 404
    
    existing.pop('_id', None)

    # Merge new fields into existing document
    data = request.get_json()
    merged = {**existing, **data}
    merged["updated_at"] = datetime.utcnow()

    # Validate merged data using Pydantic
    try:
        user = UserModel(**merged)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    
    update_data = user.model_dump(
        by_alias=True,
        exclude={"_id", "id"} # Explicitly tell Pydantic to exclude the key '_id'
    )

    # Save validated data
    db["users"].update_one({"id": user_id}, {"$set": update_data})

    return jsonify({"message": "User updated successfully"}), 200

@users_bp.route("/<string:user_id>", methods=["DELETE"])
def delete_user(user_id):
    _, db = get_db_connection(Config)
    result = db["users"].delete_one({"id": user_id})
    if result.deleted_count == 0:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User deleted successfully"}), 200
    