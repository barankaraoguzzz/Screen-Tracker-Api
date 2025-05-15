from fastapi import APIRouter, HTTPException, Depends
from app.database import sessions_collection, tenants_collection
from app.schemas import SessionCreate, Session
from datetime import datetime, timedelta
from typing import List
import uuid

router = APIRouter()

@router.post("/sessions/", response_model=Session)
async def create_session(session: SessionCreate):
    """Yeni bir session oluşturur"""
    # Tenant'ın var olduğunu kontrol et
    tenant = await tenants_collection.find_one({"id": session.tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    session_dict = session.dict()
    session_dict["id"] = str(uuid.uuid4())
    session_dict["created_at"] = datetime.utcnow()
    session_dict["expires_at"] = datetime.utcnow() + timedelta(days=30)  # 30 günlük session
    session_dict["is_active"] = True
    
    result = await sessions_collection.insert_one(session_dict)
    created_session = await sessions_collection.find_one({"_id": result.inserted_id})
    return created_session

@router.get("/sessions/{session_id}", response_model=Session)
async def get_session(session_id: str):
    """Belirli bir session'ı getirir"""
    session = await sessions_collection.find_one({"id": session_id})
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/tenants/{tenant_id}/sessions/", response_model=List[Session])
async def get_tenant_sessions(tenant_id: str):
    """Bir tenant'a ait tüm sessionları listeler"""
    # Tenant'ın var olduğunu kontrol et
    tenant = await tenants_collection.find_one({"id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    sessions = []
    cursor = sessions_collection.find({"tenant_id": tenant_id})
    async for document in cursor:
        sessions.append(document)
    return sessions 