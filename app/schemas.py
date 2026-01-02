from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from . enums import UserRole

class UserCreate(BaseModel):
    name : str
    email : EmailStr
    password : str
    role : UserRole = UserRole.customer

class UserOut(BaseModel):
    id : int
    email : EmailStr
    role : str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

class CategoryCreate(BaseModel):
    name: str

class CategoryUpdate(BaseModel):
    name: str

class CategoryOut(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token : str
    token_type : str

class TokenData(BaseModel):
    id : Optional[int] = None
    role : Optional[str] = None