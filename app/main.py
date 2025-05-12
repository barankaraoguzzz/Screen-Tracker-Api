from fastapi import FastAPI
from app.routers import events
from app.middleware import error_handling_middleware

app = FastAPI()

# Middleware ekleme
app.middleware("http")(error_handling_middleware)

# Router ekleme
app.include_router(events.router)

@app.get("/")
def read_root():
    return {"message": "Screen Tracker API'ye hoş geldiniz!"} 