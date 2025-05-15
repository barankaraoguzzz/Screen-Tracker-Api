# Event ile ilgili endpointler burada tanımlanacak 

from fastapi import APIRouter, HTTPException, Depends
from app.database import screens_collection, events_collection, sessions_collection
from app.schemas import EventTrack
from datetime import datetime
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/events/track_screen")
async def track_screen(screen_token: str, session_id: str):
    """Ekran izleme eventi oluşturur"""
    # Session'ı kontrol et
    session = await sessions_collection.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Session'ın aktif olup olmadığını kontrol et
    if not session.get("is_active", False):
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Screen'i kontrol et
    screen = await screens_collection.find_one({"screen_token": screen_token})
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # Event oluştur
    event = {
        "tenant_id": session["tenant_id"],
        "session_id": session_id,
        "screen_token": screen_token,
        "event_name": "screen_view",
        "timestamp": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
    
    await events_collection.insert_one(event)
    return {"message": "Screen tracked successfully"}

@router.post("/events/track_event")
async def track_event(event: EventTrack):
    """Olay izleme eventi oluşturur"""
    # Session'ı kontrol et
    session = await sessions_collection.find_one({"id": event.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Session'ın aktif olup olmadığını kontrol et
    if not session.get("is_active", False):
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Screen'i kontrol et
    screen = await screens_collection.find_one({"screen_token": event.screen_token})
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # Event oluştur
    event_dict = event.dict()
    event_dict["tenant_id"] = session["tenant_id"]
    event_dict["timestamp"] = event_dict.get("timestamp", datetime.utcnow())
    event_dict["created_at"] = datetime.utcnow()
    
    await events_collection.insert_one(event_dict)
    return {"message": "Event tracked successfully"} 