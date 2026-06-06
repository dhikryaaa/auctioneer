import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import DateTime, func

class User(SQLModel, table=True):
    __tablename__ = 'users'
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(index=True, nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    role: str = Field(default='user')
    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    refresh_token: list["RefreshToken"] = Relationship(
        back_populates='user', 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
class RefreshToken(SQLModel, table=True):
    __tablename__ = 'refresh_tokens'
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key='users.id', index=True, nullable=False)
    token_hash: str = Field(nullable=False)
    created_at: datetime = Field(sa_column=Column(DateTime, server_default=func.now()))
    expires_at: datetime = Field(nullable=False)
    user: Optional[User] = Relationship(back_populates='refresh_token')
    