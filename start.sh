#!/bin/bash

# Uvicorn'u doğrudan başlat, Railway zaten $PORT'u sağlam veriyor
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers
