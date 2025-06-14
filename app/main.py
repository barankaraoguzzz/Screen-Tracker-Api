from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import events, sessions, auth, projects
from app.middleware import error_handling_middleware
from app.auth import get_current_user
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title="Screen Tracker API",
    description="API for tracking screen events and sessions with role-based access control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# HTTPS proxy bilgilerini ve güvenilir domainleri tanımla
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["peekevent.xyz", "*.peekevent.xyz", "localhost"]
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik origin'ler belirtilmeli
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware ekleme
app.middleware("http")(error_handling_middleware)

# Router'ları ekleme
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"], dependencies=[Depends(get_current_user)])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"], dependencies=[Depends(get_current_user)])
app.include_router(events.router, prefix="/api", tags=["Events"], dependencies=[Depends(get_current_user)])

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Screen Tracker API'ye hoş geldiniz!",
        "docs": "/docs",
        "redoc": "/redoc"
    } 