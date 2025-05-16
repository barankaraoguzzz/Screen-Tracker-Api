# Event ile ilgili endpointler burada tanımlanacak 

from fastapi import APIRouter, HTTPException, Depends, status, Header, Query
from app.database import screens_collection, events_collection, sessions_collection, projects_collection
from app.schemas import EventTrack
from app.auth import get_current_user, verify_project_access, verify_project_auth
from typing import List, Optional
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import uuid

router = APIRouter()

async def verify_project_access(tenant_id: str, project_id: str, bundle_id: str):
    """Proje erişimini doğrular"""
    project = await projects_collection.find_one({
        "id": project_id,
        "tenant_id": tenant_id,
        "bundle_id": bundle_id,
        "is_active": True
    })
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid project access"
        )
    return project

@router.post("/track_screen", response_model=EventTrack, dependencies=[])
async def track_screen(
    event: EventTrack,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    x_project_id: str = Header(..., alias="X-Project-Id"),
    x_bundle_id: str = Header(..., alias="X-Bundle-Id")
):
    """Ekran eventlerini kaydeder"""
    # Proje erişimini doğrula
    await verify_project_auth(
        tenant_id=x_tenant_id,
        project_id=x_project_id,
        bundle_id=x_bundle_id
    )
    
    event_data = event.dict()
    event_data["tenant_id"] = x_tenant_id
    event_data["project_id"] = x_project_id
    event_data["bundle_id"] = x_bundle_id
    event_data["timestamp"] = event_data.get("timestamp") or datetime.utcnow()
    
    await events_collection.insert_one(event_data)
    return event_data

@router.get("/track_screen", response_model=List[EventTrack])
async def get_track_screen_events(
    session_id: str,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    x_project_id: str = Header(..., alias="X-Project-Id"),
    current_user: dict = Depends(get_current_user)
):
    """Belirli bir session'a ait ekran eventlerini listeler"""
    if current_user["tenant_id"] != x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tenant's events"
        )
    
    events = await events_collection.find({
        "tenant_id": x_tenant_id,
        "project_id": x_project_id,
        "session_id": session_id,
        "event_name": "screen_view"  # Ekran görüntüleme eventlerini filtrele
    }).to_list(length=100)
    return events

@router.post("/events", response_model=EventTrack, dependencies=[])
async def track_event(
    event: EventTrack,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    x_project_id: str = Header(..., alias="X-Project-Id"),
    x_bundle_id: str = Header(..., alias="X-Bundle-Id")
):
    """Yeni bir event kaydeder"""
    # Proje erişimini doğrula
    await verify_project_auth(
        tenant_id=x_tenant_id,
        project_id=x_project_id,
        bundle_id=x_bundle_id
    )
    
    event_data = event.dict()
    event_data["tenant_id"] = x_tenant_id
    event_data["project_id"] = x_project_id
    event_data["bundle_id"] = x_bundle_id
    if not event_data.get("timestamp"):
        event_data["timestamp"] = datetime.utcnow()
    
    await events_collection.insert_one(event_data)
    return event_data

@router.get("/session_events", response_model=List[EventTrack])
async def get_session_events(
    session_id: str,
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Belirli bir session'a ait tüm eventleri listeler"""
    events = await events_collection.find({
        "tenant_id": current_user["tenant_id"],
        "project_id": project_id,
        "session_id": session_id
    }).to_list(length=100)
    return events

@router.get("/time_events", response_model=List[EventTrack])
async def get_time_based_events(
    project_id: str,
    time_range: str = Query(..., description="Time range: '1d', '1w', '1m', '3m'"),
    current_user: dict = Depends(get_current_user)
):
    """Belirli bir zaman aralığındaki tüm eventleri listeler
    
    - **time_range**: Zaman aralığı ('1d': son 1 gün, '1w': son 1 hafta, '1m': son 1 ay, '3m': son 3 ay)
    """
    now = datetime.utcnow()
    time_ranges = {
        "1d": now - timedelta(days=1),
        "1w": now - timedelta(weeks=1),
        "1m": now - timedelta(days=30),
        "3m": now - timedelta(days=90)
    }
    
    if time_range not in time_ranges:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time range. Use '1d', '1w', '1m', or '3m'"
        )
    
    events = await events_collection.find({
        "tenant_id": current_user["tenant_id"],
        "project_id": project_id,
        "timestamp": {"$gte": time_ranges[time_range]}
    }).to_list(length=1000)
    return events

@router.get("/device_events", response_model=List[EventTrack])
async def get_device_events(
    device_id: str,
    project_id: str,
    time_range: str = Query(..., description="Time range: '1d', '1w', '1m', '3m'"),
    current_user: dict = Depends(get_current_user)
):
    """Belirli bir cihaza ait, belirli bir zaman aralığındaki tüm eventleri listeler
    
    - **time_range**: Zaman aralığı ('1d': son 1 gün, '1w': son 1 hafta, '1m': son 1 ay, '3m': son 3 ay)
    """
    now = datetime.utcnow()
    time_ranges = {
        "1d": now - timedelta(days=1),
        "1w": now - timedelta(weeks=1),
        "1m": now - timedelta(days=30),
        "3m": now - timedelta(days=90)
    }
    
    if time_range not in time_ranges:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time range. Use '1d', '1w', '1m', or '3m'"
        )
    
    # Önce cihaza ait sessionları bul
    sessions = await sessions_collection.find({
        "tenant_id": current_user["tenant_id"],
        "project_id": project_id,
        "device_id": device_id
    }).to_list(length=100)
    
    session_ids = [session["id"] for session in sessions]
    
    # Bu sessionlara ait eventleri getir
    events = await events_collection.find({
        "tenant_id": current_user["tenant_id"],
        "project_id": project_id,
        "session_id": {"$in": session_ids},
        "timestamp": {"$gte": time_ranges[time_range]}
    }).to_list(length=1000)
    return events 