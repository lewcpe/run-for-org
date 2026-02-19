from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import httpx
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)
from . import crud, models, config
from .database import get_db

settings = config.get_settings()
security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.RUNORG_JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.RUNORG_JWT_SECRET, algorithm=settings.RUNORG_JWT_ALGORITHM)
    return encoded_jwt

# Simple in-memory cache for OIDC config
_oidc_config_cache = {}

def get_oidc_config_url(issuer: str) -> str:
    """Discovers the authorization endpoint from the issuer."""
    if not issuer:
        return ""
        
    if issuer in _oidc_config_cache:
        return _oidc_config_cache[issuer].get("authorization_endpoint", "")
        
    discovery_url = f"{issuer}/.well-known/openid-configuration"
    try:
        with httpx.Client() as client:
            resp = client.get(discovery_url, timeout=5.0)
            if resp.status_code == 200:
                config = resp.json()
                _oidc_config_cache[issuer] = config
                return config.get("authorization_endpoint", "")
    except Exception as e:
        logger.error(f"Failed to discover OIDC config for {issuer}: {e}")
        
    return ""

def verify_oidc_token(token: str) -> dict:
    """Verifies the OIDC token with the provider's JWKS."""
    if not settings.OIDC_ISSUER:
        raise ValueError("OIDC_ISSUER not configured")
        
    discovery_url = f"{settings.OIDC_ISSUER}/.well-known/openid-configuration"
    jwks_client = httpx.Client()
    try:
         resp = jwks_client.get(discovery_url)
         resp.raise_for_status()
         oidc_config = resp.json()
         jwks_uri = oidc_config["jwks_uri"]
         
         jwks_resp = jwks_client.get(jwks_uri)
         jwks_resp.raise_for_status()
         # Check if 'keys' is in response
         jwks = jwks_resp.json()
         
         return jwt.decode(
             token,
             jwks,
             algorithms=settings.OIDC_ALGORITHMS,
             audience=settings.OIDC_AUDIENCE,
             issuer=settings.OIDC_ISSUER
         )
    finally:
        jwks_client.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify internal JWT
        payload = jwt.decode(
            token, 
            settings.RUNORG_JWT_SECRET, 
            algorithms=[settings.RUNORG_JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
        email = email.lower()
        
    except (JWTError, httpx.HTTPError) as e:
        logger.error(f"Auth error: {e}")
        raise credentials_exception
        
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        user = crud.create_user(db, email=email)
        crud.create_audit_log(db, user_id=user.id, message="User created via login")
        
    return user
