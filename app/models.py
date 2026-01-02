from enum import Enum
from sqlalchemy import TIMESTAMP, Boolean, Column, DateTime, Integer, String, func, text
from sqlalchemy import Enum as SQLEnum
from . database import Base
from . enums import UserRole

class User(Base):

    __tablename__ = "users"

    id = Column(Integer,primary_key = True,nullable = False)
    name = Column(String(100),nullable = False)
    email = Column(String,nullable = False,unique = True,index=True)
    hashed_password = Column(String(255),nullable = False)

    role = Column(
        SQLEnum(UserRole, name="user_role"), 
        nullable=False,
        server_default=UserRole.customer.value
    )
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True),nullable=False,server_default=text("now()"),onupdate=func.now()
)
    
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, unique=True, index=True)

    is_active = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(TIMESTAMP(timezone=True),nullable=False,server_default=text("now()")
    )
