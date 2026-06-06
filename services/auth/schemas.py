from pydantic import BaseModel, EmailStr
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        
class UserStatusResponse(BaseModel):
    id: str
    name: str
    role: str