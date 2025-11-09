from pydantic import BaseModel, Field
from datetime import Dict, Any
from datetime import datetime

class SegmentModel(BaseModel):
    _id: str
    name: str
    definition: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)