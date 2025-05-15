from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    get_current_owner,
    get_current_admin
)
from app.database import tenants_collection, users_collection
from app.schemas import Token, TenantCreate, Tenant, UserCreate, User, TokenData, UserRole
import uuid
from datetime import datetime
from typing import List

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
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await users_collection.insert_one(user_data)
    
    return tenant_data

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Tenant girişi yapar ve JWT token döner"""
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["id"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Giriş yapmış tenant'ın bilgilerini getirir"""
    return current_user

@router.post("/users", response_model=User)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(get_current_admin)
):
    # Email kontrolü
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Yeni kullanıcı oluştur
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "tenant_id": current_user["tenant_id"],
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": get_password_hash(user.password),
        "role": user.role,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await users_collection.insert_one(user_data)
    
    return user_data

@router.get("/users", response_model=List[User])
async def list_users(current_user: dict = Depends(get_current_admin)):
    users = await users_collection.find({"tenant_id": current_user["tenant_id"]}).to_list(length=100)
    return users 