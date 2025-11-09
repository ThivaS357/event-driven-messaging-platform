from .webhooks import webhook_bp
from .api import api_bp # This now imports the master API blueprint

def register_blueprints(app):
    app.register_blueprint(webhook_bp)
    app.register_blueprint(api_bp)