from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class SegmentModel(BaseModel):
    id: str = Field(..., alias="_id")
    topic: str
    rule: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "dance_subscribers",
                "topic": "DANCE",
                "rule": {"topic": "DANCE"}
            }
        }