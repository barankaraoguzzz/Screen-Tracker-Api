from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from app.database import sessions_collection, tenants_collection, projects_collection
from app.schemas import SessionCreate, Session
from app.auth import get_current_user, verify_project_auth
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

router = APIRouter()

@router.post("/create-session", response_model=Session, dependencies=[])
async def create_session(
    session: SessionCreate,
    x_tenant_id: str = Header(..., alias="X-Tenant-Id"),
    x_project_id: str = Header(..., alias="X-Project-Id"),
    x_bundle_id: str = Header(..., alias="X-Bundle-Id")
):
    """Yeni bir oturum oluşturur
    
    Bu endpoint, yeni bir kullanıcı oturumu oluşturur. Oturum, belirtilen tenant, proje ve bundle ID'leri ile ilişkilendirilir.
    JWT token gerektirmez çünkü bu endpoint genellikle uygulama başlatıldığında çağrılır.
    
    - **device_id**: Cihazın benzersiz tanımlayıcısı
    - **app_version**: Uygulama versiyonu
    
    Header'lar:
    - **X-Tenant-Id**: Tenant ID
    - **X-Project-Id**: Proje ID
    - **X-Bundle-Id**: Bundle ID
    """
    # Proje erişimini doğrula
    await verify_project_auth(
        tenant_id=x_tenant_id,
        project_id=x_project_id,
        bundle_id=x_bundle_id
    )
    
    session_data = session.dict()
    session_data["id"] = str(uuid.uuid4())
    session_data["tenant_id"] = x_tenant_id
    session_data["project_id"] = x_project_id
    session_data["bundle_id"] = x_bundle_id
    session_data["created_at"] = datetime.utcnow()
    session_data["expires_at"] = datetime.utcnow() + timedelta(hours=24)
    session_data["is_active"] = True
    
    await sessions_collection.insert_one(session_data)
    return session_data

@router.get("/sessions", response_model=List[Session])
async def get_tenant_sessions(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Bir tenant'a ait belirli bir projenin sessionlarını listeler
    
    Bu endpoint, JWT token'dan alınan tenant_id ile path'teki tenant_id'nin eşleştiğini kontrol eder
    ve belirtilen projeye ait sessionları listeler.
    
    - **tenant_id**: Path'te belirtilen tenant ID (JWT token'daki tenant_id ile eşleşmeli)
    - **project_id**: Sessionları filtrelemek için proje ID
    
    Not: Tenant ID JWT token'dan alınır, header'da istenmez.
    """
    
    # Projenin tenant'a ait olduğunu kontrol et
    project = await projects_collection.find_one({
        "id": project_id,
        "tenant_id": current_user["tenant_id"],
        "is_active": True
    })
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not accessible"
        )
    
    # Sessionları getir
    sessions = await sessions_collection.find({
        "tenant_id": current_user["tenant_id"],
        "project_id": project_id
    }).to_list(length=100)
    
    return sessions 

@router.get("/sessions/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Belirli bir oturumun detaylarını getirir
    
    Bu endpoint, JWT token ile doğrulanmış kullanıcının tenant'ına ait,
    belirli bir session'ın detaylarını getirir.
    
    - **session_id**: Detayları getirilecek session'ın ID'si
    
    Not: Tenant ID JWT token'dan alınır, header'da istenmez.
    """
    session = await sessions_collection.find_one({"id": session_id})
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session["tenant_id"] != current_user["tenant_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    return session

@router.get("/device_sessions", response_model=List[Session])
async def get_device_sessions(
    device_id: str,
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Belirli bir cihaza ait tüm sessionları listeler
    
    Bu endpoint, JWT token ile doğrulanmış kullanıcının tenant'ına ait,
    belirli bir cihazın tüm sessionlarını listeler.
    
    - **device_id**: Sessionları filtrelemek için cihaz ID
    - **project_id**: Sessionları filtrelemek için proje ID
    
    Not: Tenant ID JWT token'dan alınır, header'da istenmez.
    """
    sessions = await sessions_collection.find({
        "tenant_id": current_user["tenant_id"],
        "project_id": project_id,
        "device_id": device_id
    }).to_list(length=100)
    return sessions

@router.get("/time_sessions", response_model=List[Session])
async def get_time_based_sessions(
    project_id: str,
    time_range: str = Query(..., description="Time range: '1d', '1w', '1m', '3m'"),
    current_user: dict = Depends(get_current_user)
):
    """Belirli bir zaman aralığındaki tüm sessionları listeler
    
    Bu endpoint, JWT token ile doğrulanmış kullanıcının tenant'ına ait,
    belirli bir zaman aralığındaki tüm sessionları listeler.
    
    - **project_id**: Sessionları filtrelemek için proje ID
    - **time_range**: Zaman aralığı ('1d': son 1 gün, '1w': son 1 hafta, '1m': son 1 ay, '3m': son 3 ay)
    
    Not: Tenant ID JWT token'dan alınır, header'da istenmez.
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
    
    # Projenin tenant'a ait olduğunu kontrol et
    project = await projects_collection.find_one({
        "id": project_id,
        "tenant_id": current_user["tenant_id"],
        "is_active": True
    })
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or not accessible"
        )
    
    # Sessionları getir
    sessions = await sessions_collection.find({
        "tenant_id": current_user["tenant_id"],
        "project_id": project_id,
        "created_at": {"$gte": time_ranges[time_range]}
    }).to_list(length=1000)
    
    return sessions