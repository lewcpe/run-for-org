from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
import httpx
import logging
from .. import config, auth, crud, models
from ..database import get_db
from sqlalchemy.orm import Session
from datetime import datetime
from jose import jwt

logger = logging.getLogger(__name__)
settings = config.get_settings()

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.get("/callback")
async def auth_callback(request: Request, code: str, state: str = None, db: Session = Depends(get_db)):
    """
    Exchange authorization code for access token.
    This endpoint is called by the frontend or OIDC provider redirect.
    """
    if not settings.OIDC_ISSUER or not settings.OIDC_CLIENT_ID or not settings.OIDC_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OIDC is not configured on the backend."
        )

    token_endpoint = f"{settings.OIDC_ISSUER}/token"
    
    # Verify OIDC_CALLBACK_URL is set or derive from request
    redirect_uri = settings.OIDC_CALLBACK_URL or str(request.url_for("auth_callback"))
    if not redirect_uri:
        # Fallback or error? better to error to be explicit
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OIDC_CALLBACK_URL is not configured and could not be derived."
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": settings.OIDC_CLIENT_ID,
                    "client_secret": settings.OIDC_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            token_data = response.json()
            
            # Optionally: validated the token immediately?
            # yes, we can return it. Frontend will use it in Authorization header.
            
            # 1. Validate OIDC ID Token
            id_token = token_data.get("id_token")
            if not id_token:
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No ID token returned from provider"
                )
            
            try:
                oidc_claims = auth.verify_oidc_token(id_token)
            except Exception as e:
                logger.error(f"OIDC validation failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to validate OIDC token"
                )
            
            # 2. Extract email and get/create user
            email = oidc_claims.get("email")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email not found in OIDC token"
                )
            
            user = crud.get_user_by_email(db, email=email)
            if not user:
                user = crud.create_user(db, email=email)
                crud.create_audit_log(db, user_id=user.id, message="User created via OIDC login")
            
            # 3. Issue Internal JWT
            access_token = auth.create_access_token(data={"sub": user.email})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "email": user.email,
                    "firstname": user.firstname,
                    "lastname": user.lastname
                }
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"OIDC Token Exchange failed: {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange code for token"
        )
    except Exception as e:
        logger.error(f"OIDC Callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authentication error"
        )
