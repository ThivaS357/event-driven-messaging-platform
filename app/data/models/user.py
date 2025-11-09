from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime
import re

class UserModel(BaseModel):
    id: str = Field(..., alias="_id" ,description="Phone number in E.164 format (e.g., +14155552671)")
    wa_id: Optional[str] = Field(None, description="WhatsApp ID")
    name: Optional[str] = Field(None, description="User's name")
    attributes: Dict[str, Any] = {}
    consent_state: str = Field(default="STARTED",pattern="^(STARTED|STOPPED)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,   
        "extra": "ignore"
    }
    
    @field_validator('id')
    @classmethod
    def validate_phone_number(cls, value):
        if not re.match(r"^\+[1-9]\d{1,14}$", value):
            raise ValueError("Phone number must be in E.164 format (e.g., +14155552671)")
        return value