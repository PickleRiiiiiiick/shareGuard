# src/api/middleware/auth.py
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from functools import wraps
import jwt
from src.db.database import SessionLocal
from src.db.models.auth import ServiceAccount, AuthSession
from config.settings import SECURITY_CONFIG
from datetime import datetime
from src.utils.logger import setup_logger

# Set up logger
logger = setup_logger('auth_middleware')

security = HTTPBearer()

async def get_current_service_account(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate token and return associated service account"""
    logger.debug(f"Validating token: {credentials.credentials[:20]}...")
    
    db = SessionLocal()
    try:
        # Check active session first
        logger.debug("Checking for active session...")
        session = db.query(AuthSession).filter(
            AuthSession.token == credentials.credentials,
            AuthSession.is_active == True
        ).first()
        
        if not session:
            logger.warning("No active session found")
            raise HTTPException(401, "Invalid token")
        
        logger.debug(f"Found active session: {session.id}")
        logger.debug(f"Session expires at: {session.expires_at}")
        
        # Check session expiration
        if session.expires_at < datetime.utcnow():
            logger.warning("Session has expired")
            session.is_active = False
            db.commit()
            raise HTTPException(401, "Token expired")
            
        try:
            # Validate JWT and decode payload
            logger.debug("Attempting JWT validation...")
            payload = jwt.decode(
                credentials.credentials,
                SECURITY_CONFIG["secret_key"],
                algorithms=[SECURITY_CONFIG["algorithm"]]
            )
            logger.debug(f"JWT validation successful: {payload}")
            
            # Convert string ID back to integer
            try:
                account_id = int(payload["sub"])
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting subject to integer: {str(e)}")
                raise HTTPException(401, "Invalid token format")
                
            # Get service account
            logger.debug(f"Looking up service account: {account_id}")
            service_account = db.query(ServiceAccount).get(account_id)
            
            if not service_account or not service_account.is_active:
                logger.warning(f"Service account not found or inactive: {account_id}")
                raise HTTPException(401, "Invalid account")
                
            logger.debug(f"Successfully validated token for account: {service_account.username}")
            return service_account
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT has expired")
            session.is_active = False
            db.commit()
            raise HTTPException(401, "Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT validation failed: {str(e)}")
            raise HTTPException(401, "Invalid token")
            
    finally:
        db.close()

def require_permissions(required_permissions: List[str]):
    """Decorator to check required permissions for endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Find request object
                request = kwargs.get('current_request')
                if not request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                
                if not request:
                    logger.error("Request object not found in kwargs or args")
                    raise HTTPException(500, "Request object not found")
                
                # Check authorization header
                auth_header = request.headers.get('Authorization')
                logger.debug(f"Auth header: {auth_header[:20] if auth_header else None}")
                
                if not auth_header:
                    logger.warning("No Authorization header found")
                    raise HTTPException(401, "Authentication required")
                
                # Validate bearer token format
                try:
                    scheme, token = auth_header.split()
                    if scheme.lower() != 'bearer':
                        raise ValueError("Invalid scheme")
                except ValueError:
                    raise HTTPException(401, "Invalid authentication scheme")
                
                # Create credentials and validate
                credentials = HTTPAuthorizationCredentials(
                    scheme=scheme,
                    credentials=token
                )
                
                service_account = await get_current_service_account(credentials)
                
                if not service_account:
                    logger.warning("No service account returned from validation")
                    raise HTTPException(401, "Authentication required")
                
                # Check permissions
                account_permissions = service_account.permissions or []
                logger.debug(f"Account permissions: {account_permissions}")
                logger.debug(f"Required permissions: {required_permissions}")
                
                if not all(p in account_permissions for p in required_permissions):
                    logger.warning(f"Insufficient permissions for {service_account.username}")
                    raise HTTPException(403, "Insufficient permissions")
                
                request.state.service_account = service_account
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Error in permission check")
                raise HTTPException(500, f"Authorization error: {str(e)}")
                
        return wrapper
    return decorator

class AuthMiddleware:
    """Middleware for handling authentication on all routes"""
    
    async def __call__(self, request: Request, call_next):
        try:
            # Skip auth for public endpoints
            if request.url.path in ["/api/v1/auth/login", "/health", "/"]:
                return await call_next(request)

            auth_header = request.headers.get('Authorization')
            logger.debug(f"Processing request to {request.url.path}")
            logger.debug(f"Auth header: {auth_header[:20] if auth_header else None}")

            if not auth_header:
                logger.warning("No Authorization header in request")
                raise HTTPException(401, "Authentication required")

            # Validate bearer token format
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != 'bearer':
                    raise ValueError("Invalid scheme")
            except ValueError:
                raise HTTPException(401, "Invalid authentication scheme")

            credentials = HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
            
            # Validate token and get account
            service_account = await get_current_service_account(credentials)
            request.state.service_account = service_account
            
            response = await call_next(request)
            return response

        except HTTPException as e:
            logger.error(f"HTTP error in middleware: {e.status_code} - {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.exception("Unexpected error in middleware")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Internal server error: {str(e)}"}
            )