from fastapi import FastAPI, Depends, HTTPException, Request 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer
from api.routes import scan_routes, target_routes, auth_routes
from api.routes import folder_routes, alert_routes, health_routes
from db.database import init_db
from core.scanner import ShareGuardScanner
from api.middleware.auth import AuthMiddleware
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer()

app = FastAPI(
    title="ShareGuard API",
    description="API for scanning and monitoring Windows file system permissions",
    version="1.0.0"
    # Removed these lines to enable the default docs
    # docs_url=None,   
    # redoc_url=None   
)

# Get the absolute path to the dist directory
current_dir = Path(__file__).parent
dist_dir = current_dir / "web" / "dist"

# CORS middleware should be first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for WebSocket connections
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Debug requests middleware
@app.middleware("http")
async def debug_requests(request: Request, call_next):
    logger.info(f">>> Request: {request.method} {request.url.path}")
    logger.info(f">>> Headers: {dict(request.headers)}")
    
    try:
        # Try to read body for debugging
        body = await request.body()
        if body:
            logger.info(f">>> Body: {body.decode()}")
    except Exception as e:
        logger.error(f"Error reading body: {e}")
    
    response = await call_next(request)
    logger.info(f"<<< Response Status: {response.status_code}")
    
    return response

# Initialize scanner
scanner = ShareGuardScanner()

# Include routers before auth middleware
app.include_router(
    auth_routes.router,
    prefix="/api/v1",
    tags=["authentication"]
)
app.include_router(
    scan_routes.router,
    prefix="/api/v1",
    tags=["scanning"]
)
app.include_router(
    target_routes.router,
    prefix="/api/v1",
    tags=["targets"]
)
app.include_router(
    folder_routes.router,
    prefix="/api/v1",
    tags=["folders"]
)
app.include_router(
    alert_routes.router,
    prefix="/api/v1",
    tags=["alerts"]
)
app.include_router(
    health_routes.router,
    prefix="/api/v1/health",
    tags=["health"]
)

# Mount frontend files if the directory exists
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True))

# Auth middleware should be last
app.middleware("http")(AuthMiddleware())

# Keep the rest of the file unchanged
@app.get("/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="ShareGuard API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    openapi_schema = get_openapi(
        title="ShareGuard API",
        version="1.0.0",
        description="API for scanning and monitoring Windows file system permissions",
        routes=app.routes,
    )
    return openapi_schema

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    init_db()
    
    # Start notification service
    from src.services.notification_service import notification_service
    await notification_service.start_service()
    
    # Start change monitor service
    from src.services.change_monitor import change_monitor
    # Get all scan targets and start monitoring them
    from src.db.database import get_db_sync
    from src.db.models import ScanTarget
    try:
        db = next(get_db_sync())
        targets = db.query(ScanTarget).filter(ScanTarget.is_active == True).all()
        paths = [target.path for target in targets]
        if paths:
            await change_monitor.start_monitoring(paths)
            logger.info(f"Started monitoring {len(paths)} paths for changes")
    except Exception as e:
        logger.error(f"Error starting change monitor: {str(e)}")
    finally:
        db.close()
    
    logger.info("ShareGuard API started successfully")
    logger.info("Configured CORS origins: ['http://localhost:5173', 'http://localhost:8000']")

@app.on_event("shutdown")
async def shutdown_event():
    # Stop notification service
    from src.services.notification_service import notification_service
    await notification_service.stop_service()
    
    # Stop change monitor service
    from src.services.change_monitor import change_monitor
    await change_monitor.stop_monitoring()
    
    logger.info("ShareGuard API shutdown complete")
