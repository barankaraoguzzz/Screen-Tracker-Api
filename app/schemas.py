# Pydantic şemaları burada tanımlanacak 
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List
from datetime import datetime
import uuid
from enum import Enum

# Rol tanımlamaları
class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"

# Token modelleri
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[UserRole] = None

# Kullanıcı modelleri
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# Tenant modelleri
class TenantBase(BaseModel):
    name: str
    description: Optional[str] = None

class TenantCreate(TenantBase):
    owner_email: EmailStr
    owner_password: str
    owner_full_name: str

class Tenant(TenantBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# Session modelleri
class SessionBase(BaseModel):
    tenant_id: str
    device_id: str
    app_version: str

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    is_active: bool = True

# Event modelleri
class EventTrack(BaseModel):
    screen_token: str
    session_id: str
    event_name: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict] = None 