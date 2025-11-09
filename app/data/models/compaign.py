from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime

class CompaignModel(BaseModel):
    _id: str
    topic: str
    template_id: str
    segment_id: str
    schedule: Dict[str, Optional[str]] = Field(
        default={"start_time": None, "end_time": None}
    )
    status: str = Field(default="scheduled", pattern="^(scheduled|running|paused|completed)$")
    rate_limit: Optional[int] = 100
    quiet_hours: Dict[str, str] = Field(default={"start": "22:00", "end": "07:00"})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)