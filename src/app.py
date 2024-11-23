# src/app.p
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import scan_routes, target_routes, auth_routes
from db.database import init_db
from core.scanner import ShareGuardScanner
from config.settings import API_CONFIG
from api.middleware.auth import AuthMiddleware

# Create FastAPI app
app = FastAPI(
    title="ShareGuard API",
    description="API for scanning and monitoring Windows file system permissions",
    version="1.0.0"
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG['cors_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(AuthMiddleware())

# Initialize scanner
scanner = ShareGuardScanner()

# Include routers
app.include_router(auth_routes.router)
app.include_router(scan_routes.router)
app.include_router(target_routes.router)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to ShareGuard API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()