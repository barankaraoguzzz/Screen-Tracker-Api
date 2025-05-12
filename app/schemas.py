# Pydantic şemaları burada tanımlanacak 
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

# Event track modeli
class EventTrack(BaseModel):
    screen_token: str
    session_id: str
    event_name: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict] = None 