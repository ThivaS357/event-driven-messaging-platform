from flask import Blueprint, jsonify
from app.services.campaign_runner import run_campaign

orchestration_bp = Blueprint("orchestration_api", __name__, url_prefix="/orchestration")

@orchestration_bp.route("/run/<string:campaign_id>", methods=["POST"])
def trigger_campaign(campaign_id):
    """
    Trigger a campaign run manually.
    """
    result = run_campaign(campaign_id)
    return jsonify(result), 200
