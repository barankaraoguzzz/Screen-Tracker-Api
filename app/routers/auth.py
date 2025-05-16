from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    get_current_owner,
    get_current_admin
)
from app.database import (
    tenants_collection, 
    users_collection, 
    projects_collection,
    invitation_tokens_collection
)
from app.schemas import (
    Token, 
    TenantCreate, 
    Tenant, 
    UserCreate, 
    User, 
    TokenData, 
    UserRole,
    UserInvite,
    LoginRequest
)
import uuid
from typing import List
import secrets

router = APIRouter()

@router.post("/register", response_model=Tenant)
async def register_tenant(tenant: TenantCreate):
    """Yeni bir tenant kaydı oluşturur"""
    # Email kontrolü
    existing_tenant = await tenants_collection.find_one({"email": tenant.email})
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Tenant oluştur
    tenant_id = str(uuid.uuid4())
    tenant_data = {
        "id": tenant_id,
        "name": tenant.name,
        "description": tenant.description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await tenants_collection.insert_one(tenant_data)
    
    # Owner kullanıcısını oluştur
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "tenant_id": tenant_id,
        "email": tenant.owner_email,
        "full_name": tenant.owner_full_name,
        "hashed_password": get_password_hash(tenant.owner_password),
        "role": UserRole.OWNER,
        "project_permissions": [],  # Owner tüm projelere erişebilir
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await users_collection.insert_one(user_data)
    
    return tenant_data

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """Kullanıcı girişi yapar ve JWT token döner"""
    user = await users_collection.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "tenant_id": user["tenant_id"],
            "role": user["role"],
            "project_permissions": user.get("project_permissions", [])
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/invite", response_model=dict)
async def invite_user(
    invite: UserInvite,
    current_user: dict = Depends(get_current_admin)
):
    """Kullanıcı davet eder ve davet linki oluşturur"""
    # Email kontrolü
    existing_user = await users_collection.find_one({"email": invite.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Proje erişim kontrolü
    for project_id in invite.project_ids:
        project = await projects_collection.find_one({
            "id": project_id,
            "tenant_id": current_user["tenant_id"]
        })
        if not project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project {project_id} not found or not accessible"
            )
    
    # Davet token'ı oluştur
    invitation_token = secrets.token_urlsafe(32)
    invitation_data = {
        "token": invitation_token,
        "email": invite.email,
        "tenant_id": current_user["tenant_id"],
        "role": invite.role,
        "project_ids": invite.project_ids,
        "expires_at": datetime.utcnow() + timedelta(days=7),
        "is_used": False,
        "created_at": datetime.utcnow()
    }
    
    # Davet token'ını kaydet
    await invitation_tokens_collection.insert_one(invitation_data)
    
    # TODO: Send invitation email with registration link
    # For now, we'll just return the token
    return {
        "message": "User invited successfully",
        "invitation_token": invitation_token,
        "registration_url": f"/register?token={invitation_token}"
    }

@router.post("/register-with-invite", response_model=User)
async def register_with_invite(user: UserCreate):
    """Davet linki ile kullanıcı kaydı yapar"""
    # Davet token'ını kontrol et
    invitation = await invitation_tokens_collection.find_one({
        "token": user.invitation_token,
        "is_used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token"
        )
    
    # Email kontrolü
    if invitation["email"] != user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email does not match invitation"
        )
    
    # Kullanıcı oluştur
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "tenant_id": invitation["tenant_id"],
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": get_password_hash(user.password),
        "role": invitation["role"],
        "project_permissions": invitation["project_ids"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Davet token'ını kullanıldı olarak işaretle
    await invitation_tokens_collection.update_one(
        {"token": user.invitation_token},
        {"$set": {"is_used": True}}
    )
    
    await users_collection.insert_one(user_data)
    return user_data

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Giriş yapmış kullanıcının bilgilerini getirir"""
    return current_user

@router.get("/users", response_model=List[User])
async def list_users(current_user: dict = Depends(get_current_admin)):
    """Tenant'a ait kullanıcıları listeler"""
    users = await users_collection.find({"tenant_id": current_user["tenant_id"]}).to_list(length=100)
    return users 