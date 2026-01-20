from enum import Enum
import enum


class UserRole(str,Enum):
    admin = "admin"
    customer = "customer"

class OrderStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"
    shipped = "shipped"
    delivered = "delivered"

