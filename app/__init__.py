from flask import Flask
from flasgger import Swagger
from flask_cors import CORS
from .config import Config

from .routes import register_blueprints


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS for development to allow Swagger UI to make requests
    if app.config.get("DEBUG"):
        CORS(app)

    # Conditionally initialize Swagger UI for development mode from an external file
    if app.config.get("DEBUG"):
        app.config['SWAGGER'] = {
            'title': 'Event-Driven Messaging API',
            'uiversion': 3
        }
        Swagger(app, template_file='swagger.yml')

    register_blueprints(app)
    

    return app