from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
import datetime

class TemplateModel(BaseModel):
    _id: str
    channel: str = "whatsapp"
    locale: str = "en_US"
    content: str
    placeholders: List[str] = []
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow) 
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)