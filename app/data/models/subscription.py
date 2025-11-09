from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SubscriptionModel(BaseModel):
    _id: Optional[str] = None
    user_id: str
    topic: str
    subscribed_at: datetime = Field(default_factory=datetime.utcnow)
    unsubscribed_at: Optional[datetime] = None