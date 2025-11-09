from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class DeliveryReceiptModel(BaseModel):
    _id: Optional[str] = None
    message_sid: str
    status: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_payload: Dict[str, Any]
