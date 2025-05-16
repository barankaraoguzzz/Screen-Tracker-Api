from fastapi import APIRouter, Depends, HTTPException, status
from app.database import projects_collection, tenants_collection
from app.schemas import ProjectCreate, Project
from app.auth import get_current_user, get_current_admin
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/", response_model=Project)
async def create_project(
    project: ProjectCreate,
    current_user: dict = Depends(get_current_admin)
):
    # Bundle ID kontrolü
    existing_project = await projects_collection.find_one({
        "tenant_id": current_user["tenant_id"],
        "bundle_id": project.bundle_id
    })
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bundle ID already exists for this tenant"
        )
    
    # Yeni proje oluştur
    project_id = str(uuid.uuid4())
    project_data = {
        "id": project_id,
        "tenant_id": current_user["tenant_id"],
        "name": project.name,
        "platform": project.platform,
        "bundle_id": project.bundle_id,
        "description": project.description,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await projects_collection.insert_one(project_data)
    
    return project_data

@router.get("/", response_model=list[Project])
async def list_projects(current_user: dict = Depends(get_current_user)):
    projects = await projects_collection.find(
        {"tenant_id": current_user["tenant_id"]}
    ).to_list(length=100)
    return projects

@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    project = await projects_collection.find_one({
        "id": project_id,
        "tenant_id": current_user["tenant_id"]
    })
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project 