from flask import Blueprint

from .users import users_bp
from .subscriptions import subscriptions_bp
from .campaigns import campaigns_bp
from .ingestions import ingestion_bp
from .orchestration import orchestration_bp


# This is the master blueprint for all API routes
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Register the resource-specific blueprints to the master API blueprint
api_bp.register_blueprint(users_bp)
api_bp.register_blueprint(subscriptions_bp)
api_bp.register_blueprint(campaigns_bp)
api_bp.register_blueprint(ingestion_bp)
api_bp.register_blueprint(orchestration_bp)