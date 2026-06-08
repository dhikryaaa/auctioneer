from fastapi import Request, HTTPException, Depends
from typing import TypedDict, Annotated, Any
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from database import get_db

class UserPayload(TypedDict):
    user_id: int
    role: str


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.client

def get_current_user(request: Request) -> dict:
    user_id = request.headers.get("X-User-ID")
    role = request.headers.get("X-User-Role")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        parsed_user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"user_id": parsed_user_id, "role": role}

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return user

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
AdminUser = Annotated[dict[str, Any], Depends(require_admin)]
DB = Annotated[AsyncSession, Depends(get_db)]
HttpClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]