#src/app.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from api.schemas import ScanRequest, ScanResult, ScanJob
from api.routes import scan_routes
from db.database import get_db
from core.scanner import ShareGuardScanner

app = FastAPI(title="ShareGuard API")

# Include routers
app.include_router(scan_routes.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to ShareGuard API"}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}