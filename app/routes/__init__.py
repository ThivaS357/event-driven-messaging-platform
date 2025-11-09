from .webhooks import webhook_bp
from .api import api_bp # This now imports the master API blueprint
from .webui import webui_bp


def register_blueprints(app):
    app.register_blueprint(webhook_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(webui_bp)