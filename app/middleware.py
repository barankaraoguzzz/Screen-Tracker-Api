from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Hata yönetimi middleware
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)}) 