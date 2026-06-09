from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from database import get_db
from models import User, RefreshToken
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserOut, UserStatusResponse
from security import (hash_password, verify_password, create_access_token, new_refresh_token, hash_refresh_token)
from dependencies import get_current_user, require_admin
from config import settings
from typing import cast

router = APIRouter()

async def issue_refresh(db: AsyncSession, user: User, response: Response):
    raw_token, digest = new_refresh_token()
    
    db.add(RefreshToken(
        user_id=cast(int, user.id), 
        token_hash=digest,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_DAYS)
    ))
    
    await db.commit()
    
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,
        secure=settings.COOKIES_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 3600
    )
    
# Public endpoints
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(request: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
    )
    
    db.add(user)
    
    await db.commit()
    await db.refresh(user)
    await issue_refresh(db, user, response)
    
    return TokenResponse(access_token=create_access_token(user.id, user.role))

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    await issue_refresh(db, user, response)
    
    return TokenResponse(access_token=create_access_token(user.id, user.role))

@router.post("/refresh", response_model=TokenResponse)
async def refresh(response: Response, db: AsyncSession = Depends(get_db), refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token)))
    token = result.scalars().first()
    
    if not token or token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    user = await db.get(User, token.user_id)
    
    if user is None:
        return HTTPException(status_code=404, detail='User not found')
    
    await db.delete(token)
    await db.commit()
    await issue_refresh(db, user, response)
    
    return TokenResponse(access_token=create_access_token(user.id, user.role))

# Protected endpoints
@router.post("/logout")
async def logout(response: Response, db: AsyncSession = Depends(get_db), user=Depends(get_current_user), refresh_token: str | None = Cookie(default=None)):
    if refresh_token:
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token)))
        token = result.scalars().first()
        
        if token:
            await db.delete(token)
            await db.commit()
            
    response.delete_cookie("refresh_token")
    
    return {"detail": "Logged out"}

@router.get("/me", response_model=UserOut)
async def get_me(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    user = await db.get(User, user["user_id"])
    
    if user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    user_payload = UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at
    )
    
    return user_payload


# Admin-only endpoint
@router.get("/admin/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    user_payloads = [UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at
    ) for user in users]
    
    return user_payloads

@router.get("/admin/user_status/{user_id}", response_model=UserStatusResponse)
async def user_status(user_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    user = await db.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserStatusResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,    
    )
    
