from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr

from backend.auth.models import User, UserRole, UserProfile, SessionToken, ApiKey
from backend.auth.security import security_manager
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.RESEARCHER


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class CreateApiKeyRequest(BaseModel):
    name: str
    org_id: Optional[str] = None
    scopes: Optional[List[str]] = None


class CreateApiKeyResponse(BaseModel):
    api_key: ApiKey
    raw_secret_key: str


@router.post("/register", response_model=UserProfile, summary="Register New User Account")
async def register(req: RegisterRequest):
    # Enforce password complexity (X8)
    valid, msg = security_manager.validate_password_strength(req.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    try:
        user = security_manager.create_user(
            username=req.username,
            email=req.email,
            password=req.password,
            role=req.role,
        )
        return UserProfile(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=SessionToken, summary="User Authentication & Token Issuance")
async def login(req: LoginRequest):
    user = security_manager.authenticate(req.username_or_email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    token = security_manager.create_session_token(user)
    return token


@router.get("/me", response_model=UserProfile, summary="Get Current Authenticated Profile")
async def get_me(user: User = Depends(get_current_user)):
    return UserProfile(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/logout", summary="Logout Session & Revoke Token")
async def logout(
    authorization: Optional[str] = Header(None),
    user: User = Depends(get_current_user),
):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        security_manager.revoke_token(token)
    return {"status": "logged_out", "user_id": user.user_id}


# ─── API Key Management Endpoints (X1) ───

@router.post("/api-keys", response_model=CreateApiKeyResponse, summary="Create API Key")
async def create_api_key(req: CreateApiKeyRequest, user: User = Depends(get_current_user)):
    """Generate a programmatic API key for SDK / CLI / CI integration."""
    raw_key, api_key = security_manager.create_api_key(
        user_id=user.user_id,
        name=req.name,
        org_id=req.org_id,
        scopes=req.scopes,
    )
    return CreateApiKeyResponse(api_key=api_key, raw_secret_key=raw_key)


@router.get("/api-keys", response_model=List[ApiKey], summary="List User API Keys")
async def list_api_keys(user: User = Depends(get_current_user)):
    """List all active API keys owned by the user."""
    return security_manager.list_api_keys(user.user_id)


@router.delete("/api-keys/{key_id}", summary="Revoke API Key")
async def revoke_api_key(key_id: str, user: User = Depends(get_current_user)):
    """Revoke and deactivate an API key."""
    success = security_manager.revoke_api_key(key_id, user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found or already deactivated.")
    return {"status": "revoked", "key_id": key_id}


# ─── Enterprise SSO & SAML 2.0 Endpoints (Item 19) ───

from fastapi.responses import PlainTextResponse
from backend.auth.sso import sso_service, SSOProviderInfo, SSOLoginRequest, SSOLoginResponse


@router.get("/sso/providers", response_model=List[SSOProviderInfo], summary="List Enterprise SSO Providers")
async def list_sso_providers():
    """Returns configured enterprise SSO providers (Okta, Azure AD, Google Workspace)."""
    return sso_service.list_providers()


@router.post("/sso/login", response_model=SSOLoginResponse, summary="Authenticate via Enterprise SSO")
async def sso_login(req: SSOLoginRequest):
    """Exchanges SAML assertion or OIDC token for authenticated session with assigned RBAC role."""
    try:
        return sso_service.authenticate_sso(req)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/sso/saml/metadata.xml", summary="Download SAML 2.0 SP Metadata XML")
async def get_saml_metadata():
    """Generates official SAML 2.0 Service Provider (SP) metadata XML for enterprise IT."""
    xml_content = sso_service.generate_saml_sp_metadata_xml()
    return PlainTextResponse(
        xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="aasi_saml_sp_metadata.xml"'},
    )


