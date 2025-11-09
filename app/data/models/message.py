from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MessageModel(BaseModel):
    _id: Optional[str] = None
    campaign_id: str
    user_id: str
    template_id: str
    rendered_content: str
    twilio_sid: Optional[str] = None
    status: str = Field(default="queued")
    error_code: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
