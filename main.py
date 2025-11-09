import os
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

if os.getenv('FLASK_ENV') == 'production':
    config_class = ProductionConfig
else:
    config_class = DevelopmentConfig

app = create_app(config_class)

if __name__ == '__main__':
    app.run() 