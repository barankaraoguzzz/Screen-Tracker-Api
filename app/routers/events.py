# Event ile ilgili endpointler burada tanımlanacak 

from fastapi import APIRouter, HTTPException, Depends
from app.database import screens_collection, events_collection
from app.auth import get_current_user
from datetime import datetime
from bson.objectid import ObjectId

router = APIRouter()

# Screen track endpoint
@router.post("/api/events/track_screen")
async def track_screen(screen_token: str, session_id: str):
    screen = await screens_collection.find_one({"screen_token": screen_token})
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    tenant_id = screen["tenant_id"]
    event = {
        "tenant_id": tenant_id,
        "screen_token": screen_token,
        "session_id": session_id,
        "event_name": "screen_view",
        "timestamp": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
    await events_collection.insert_one(event)
    return {"message": "Screen tracked successfully"}

# Event track endpoint
@router.post("/api/events/track_event")
async def track_event(screen_token: str, session_id: str, event_name: str, timestamp: datetime = None, metadata: dict = None):
    screen = await screens_collection.find_one({"screen_token": screen_token})
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    tenant_id = screen["tenant_id"]
    if not timestamp:
        timestamp = datetime.utcnow()
    event = {
        "tenant_id": tenant_id,
        "screen_token": screen_token,
        "session_id": session_id,
        "event_name": event_name,
        "timestamp": timestamp,
        "metadata": metadata,
        "created_at": datetime.utcnow()
    }
    await events_collection.insert_one(event)
    return {"message": "Event tracked successfully"} 