from fastapi import APIRouter, Depends, HTTPException, Security, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.db.models.auth import ServiceAccount, AuthSession
from datetime import datetime, timedelta
import win32security
import jwt
from config.settings import SECURITY_CONFIG
from pydantic import BaseModel
from src.utils.logger import setup_logger
from typing import Optional

logger = setup_logger('auth_routes')

router = APIRouter(
    prefix="/auth",  # This is important - it will be combined with the app prefix
    tags=["authentication"]
)

# Make authentication optional for public endpoints
security = HTTPBearer(auto_error=False)

class LoginRequest(BaseModel):
    username: str
    domain: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: str
    account: dict

def validate_windows_credentials(username: str, domain: str, password: str) -> bool:
    try:
        logger.debug(f"Attempting Windows authentication for {domain}\\{username}")
        win32security.LogonUser(
            username,
            domain,
            password,
            win32security.LOGON32_LOGON_NETWORK,
            win32security.LOGON32_PROVIDER_DEFAULT
        )
        return True
    except win32security.error as e:
        logger.warning(f"Windows authentication failed for {domain}\\{username}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Windows authentication: {str(e)}")
        return False

def create_session_token(service_account: ServiceAccount) -> str:
    try:
        expiry = datetime.utcnow() + timedelta(minutes=SECURITY_CONFIG["token_expire_minutes"])
        payload = {
            "sub": str(service_account.id),
            "name": f"{service_account.domain}\\{service_account.username}",
            "exp": expiry,
            "iat": datetime.utcnow()
        }
        logger.debug(f"Creating token with payload: {payload}")
        return jwt.encode(payload, SECURITY_CONFIG["secret_key"], algorithm=SECURITY_CONFIG["algorithm"])
    except Exception as e:
        logger.error(f"Error creating session token: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating session token")

# Function to handle optional authentication
async def get_optional_auth(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    return auth.credentials if auth else None

# Login endpoint (public)
@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Login attempt for {login_data.username}@{login_data.domain}")

        # Validate Windows credentials
        if not validate_windows_credentials(login_data.username, login_data.domain, login_data.password):
            logger.warning(f"Invalid Windows credentials for {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Windows credentials"
            )

        # Check if service account exists and is active
        service_account = db.query(ServiceAccount).filter(
            ServiceAccount.username == login_data.username,
            ServiceAccount.domain == login_data.domain,
            ServiceAccount.is_active == True
        ).first()

        if not service_account:
            logger.warning(f"Service account not authorized: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Service account not authorized"
            )

        # Deactivate existing sessions
        try:
            existing_sessions = db.query(AuthSession).filter(
                AuthSession.service_account_id == service_account.id,
                AuthSession.is_active == True
            ).all()

            for session in existing_sessions:
                logger.debug(f"Deactivating existing session {session.id}")
                session.is_active = False

        except Exception as e:
            logger.error(f"Error deactivating existing sessions: {str(e)}")
            # Continue with login process even if session deactivation fails

        # Create new session
        try:
            token = create_session_token(service_account)
            expiry = datetime.utcnow() + timedelta(minutes=SECURITY_CONFIG["token_expire_minutes"])

            session = AuthSession(
                service_account_id=service_account.id,
                token=token,
                expires_at=expiry,
                is_active=True
            )

            db.add(session)
            service_account.last_login = datetime.utcnow()
            db.commit()

            logger.info(f"Login successful for {service_account.username}")
            return {
                "access_token": token,
                "token_type": "bearer",
                "expires_at": expiry.isoformat(),
                "account": {
                    "username": service_account.username,
                    "domain": service_account.domain,
                    "permissions": service_account.permissions
                }
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating new session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating session"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Logout endpoint (requires authentication)
@router.post("/logout")
async def logout(
    current_token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if not current_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        logger.info("Processing logout request")
        session = db.query(AuthSession).filter(
            AuthSession.token == current_token.credentials,
            AuthSession.is_active == True
        ).first()

        if session:
            logger.debug(f"Deactivating session {session.id}")
            session.is_active = False
            db.commit()

        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.exception("Error during logout")
        raise HTTPException(status_code=500, detail=str(e))

# Token verification endpoint (requires authentication)
@router.get("/verify")
async def verify_token(
    current_token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if not current_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        logger.debug("Processing token verification request")
        # Verify token signature and expiry
        payload = jwt.decode(
            current_token.credentials,
            SECURITY_CONFIG["secret_key"],
            algorithms=[SECURITY_CONFIG["algorithm"]]
        )

        # Check if session is active
        session = db.query(AuthSession).filter(
            AuthSession.token == current_token.credentials,
            AuthSession.is_active == True
        ).first()

        if not session:
            logger.warning("No active session found during verification")
            raise HTTPException(status_code=401, detail="Session not found or inactive")

        # Get service account
        service_account = db.query(ServiceAccount).get(int(payload["sub"]))
        if not service_account or not service_account.is_active:
            logger.warning(f"Service account not found or inactive: {payload.get('sub')}")
            raise HTTPException(status_code=401, detail="Service account not found or inactive")

        logger.info(f"Token verified successfully for {service_account.username}")
        return {
            "valid": True,
            "account": {
                "username": service_account.username,
                "domain": service_account.domain,
                "permissions": service_account.permissions
            },
            "expires_at": session.expires_at.isoformat()
        }

    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired during verification")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token during verification: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.exception("Unexpected error during token verification")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint to validate authentication
@router.get("/test", summary="Test Authentication")
async def test_auth(current_request: Request):
    """Simple endpoint to test authentication without any business logic."""
    if not hasattr(current_request.state, 'service_account'):
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "authenticated": True,
        "account": {
            "username": current_request.state.service_account.username,
            "domain": current_request.state.service_account.domain,
            "permissions": current_request.state.service_account.permissions
        }
    }
