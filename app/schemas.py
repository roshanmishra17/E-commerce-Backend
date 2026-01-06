from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, condecimal, conint
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

class ProductCreate(BaseModel):
    name : str
    slug : str
    description : Optional[str] = None
    price : condecimal(max_digits=10, decimal_places=2) # type: ignore
    category_id: int

class ProductUpdate(BaseModel):
    name : Optional[str] = None
    description : Optional[str] = None
    price : Optional[condecimal(max_digits=10, decimal_places=2)] = None # type: ignore

class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    price: float
    is_active: bool
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class InventoryCreate(BaseModel):
    product_id : int
    quantity : conint(ge=0) # type: ignore

class InventoryUpdate(BaseModel):
    quantity : conint(ge=0) # type: ignore

class InventoryOut(BaseModel):
    product_id : int
    quantity : conint(ge=0) # type: ignore
    reserved_quantity : int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CartItemAdd(BaseModel):
    product_id: int
    quantity: conint(gt=0) # type: ignore

class CartItemUpdate(BaseModel):
    quantity: conint(gt=0) # type: ignore

class CartItemOut(BaseModel):
    product_id: int
    quantity: int

class CartOut(BaseModel):
    items: list[CartItemOut]

class Token(BaseModel): 
    access_token : str
    token_type : str

class TokenData(BaseModel):
    id : Optional[int] = None
    role : Optional[str] = None