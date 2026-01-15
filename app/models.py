from enum import Enum
from sqlalchemy import TIMESTAMP, Boolean, CheckConstraint, Column, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy import Enum as SQLEnum
from . database import Base
from . enums import UserRole,OrderStatus
from sqlalchemy.orm import relationship
import enum
from sqlalchemy import Enum



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

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('now()')
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()")
    )
    cart = relationship("Cart", back_populates="user", uselist=False)
    
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, unique=True, index=True)

    is_active = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()")
    )

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100),nullable = False,unique = True,index = True)
    description = Column(Text)

    price = Column(Numeric(10, 2), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)


    is_active = Column(Boolean, nullable=False, server_default="true")

    image_url = Column(String(500), nullable=True)

    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now()
    )

    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory",back_populates="product",uselist=False)

    
    __table_args__ = (
        CheckConstraint("price >= 0", name="price_non_negative"),
    )

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True
    )

    quantity = Column(Integer,nullable=False)
    reserved_quantity = Column(Integer,nullable=False,server_default='0')

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now()
    )

    product = relationship("Product", back_populates="inventory")
    
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="reserved_quantity_non_negative"),
        CheckConstraint(
            "reserved_quantity <= quantity",
            name="reserved_lte_quantity"
        ),
    )

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),  # safer
        nullable=False,
        unique=True,
        index=True
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
        index=True
    )

    user = relationship("User", back_populates="cart")

    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"
    )

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)

    cart_id = Column(
        Integer,
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    quantity = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="unique_cart_product"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    cart = relationship("Cart", back_populates="items")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer,primary_key=True,index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id",ondelete='RESTRICT'),
        nullable=False,
        index = True
    )
    status = Column(
        Enum(OrderStatus,name="order_status"),
        nullable=False,
        server_default=OrderStatus.pending.value,
        index=True
    )

    total_amount = Column(Numeric(10,3),nullable=False)

    created_at = Column(TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now()
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    product_name = Column(String(150), nullable=False)
    product_price = Column(Numeric(10, 2), nullable=False)

    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="order_item_quantity_positive"),
    )



