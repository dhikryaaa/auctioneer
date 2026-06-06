from fastapi import Request, HTTPException, Depends

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