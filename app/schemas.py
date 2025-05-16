# Pydantic şemaları burada tanımlanacak 
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List
from datetime import datetime
import uuid
from enum import Enum
from fastapi.security import OAuth2PasswordRequestForm

# Rol tanımlamaları
class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"

# Platform tanımlamaları
class Platform(str, Enum):
    IOS = "ios"
    ANDROID = "android"

# Login formu
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Token modelleri
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[UserRole] = None
    project_permissions: List[str] = []

# Kullanıcı modelleri
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole

class UserInvite(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    project_ids: List[str] = []  # Kullanıcının erişebileceği projelerin listesi

class UserCreate(UserBase):
    password: str
    invitation_token: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    project_permissions: List[str] = []  # Kullanıcının erişebileceği projelerin listesi
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# Proje modelleri
class ProjectBase(BaseModel):
    name: str
    platform: Platform
    bundle_id: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
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
    device_id: str
    app_version: str

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    project_id: str
    bundle_id: str
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

class InvitationToken(BaseModel):
    token: str
    email: EmailStr
    tenant_id: str
    role: UserRole
    project_ids: List[str]
    expires_at: datetime
    is_used: bool = False 