import pytest
from pydantic import ValidationError
from app.data.models.user import UserModel
from app.data.models.segment import SegmentModel
from app.data.models.template import TemplateModel

def test_user_model_valid_phone():
    """Tests that a UserModel can be created with a valid E.164 phone number."""
    user_data = {"_id": "+14155552671", "name": "Test User"}
    user = UserModel(**user_data)
    assert user.id == "+14155552671"
    assert user.name == "Test User"

def test_user_model_invalid_phone():
    """Tests that creating a UserModel with an invalid phone number raises a ValidationError."""
    with pytest.raises(ValidationError):
        UserModel(_id="12345", name="Invalid User")

def test_segment_model_creation():
    """Tests successful creation of a SegmentModel."""
    segment_data = {
        "name": "Test Segment",
        "topic": "TEST",
        "rule": {"attributes.city": "Testville"}
    }
    segment = SegmentModel(**segment_data)
    assert segment.rule["attributes.city"] == "Testville"

def test_template_model_creation():
    """Tests successful creation of a TemplateModel."""
    template_data = {"content": "Hello {{name}}"}
    template = TemplateModel(**template_data)
    assert template.content == "Hello {{name}}"
