import pytest
from app import create_app
from app.config import DevelopmentConfig
from mongomock import MongoClient

@pytest.fixture(scope='module')
def app():
    """Create and configure a new app instance for each test module."""
    
    # Use a mock MongoDB client for tests
    class MockConfig(DevelopmentConfig):
        MONGO_URI = "mongodb://localhost:27017/test_db" # This will be mocked

    # Monkeypatch the get_db_connection to use mongomock
    from app.data import database
    mock_client = MongoClient()
    database.mongo_client = mock_client
    database.mongo_db = mock_client[MockConfig.MONGO_DATABASE_NAME]

    app = create_app(MockConfig)
    yield app

@pytest.fixture(scope='module')
def client(app):
    """A test client for the app."""
    return app.test_client()
