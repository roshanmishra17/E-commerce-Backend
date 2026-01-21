from typing import List, Optional
from sqlalchemy.orm import Session
from .. database import get_db
from . admin import admin_required
from fastapi import APIRouter, Depends, HTTPException,status
from .. import models
from .. oauth import get_current_active_user
from .. schemas import OrderOut, OrderUpdateStatus
from sqlalchemy.exc import SQLAlchemyError
from .. enums import OrderStatus


router = APIRouter(prefix='/orders',tags=['Orders'])

ALLOWED_TRANSITIONS = {
    OrderStatus.pending: {OrderStatus.paid, OrderStatus.cancelled},
    OrderStatus.paid: {OrderStatus.shipped, OrderStatus.cancelled},
    OrderStatus.shipped: {OrderStatus.delivered},
    OrderStatus.delivered: set(),
    OrderStatus.cancelled: set(),
}


@router.post('/',response_model=OrderOut,status_code=status.HTTP_201_CREATED)
def create_order(db : Session = Depends(get_db),current_user: models.User = Depends(get_current_active_user)):
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    try:
        total_amount = 0
        order_items : List[models.OrderItem] = []

        for cart_item in cart.items:

            inventory = db.query(models.Inventory).filter(
                models.Inventory.product_id == cart_item.product_id
            ).with_for_update().first()

            if not inventory:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inventory not found"
                )
            if inventory.reserved_quantity < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inventory mismatch"
                )
            product = db.query(models.Product).filter(models.Product.id == cart_item.product_id).first()
            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Product"
                )
            inventory.quantity -= cart_item.quantity
            inventory.reserved_quantity -= cart_item.quantity

            line_total = product.price * cart_item.quantity
            total_amount += line_total

            order_items.append(
                models.OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    product_price=product.price,
                    quantity=cart_item.quantity
                )
            )

        order = models.Order(
            user_id=current_user.id,
            total_amount=total_amount
        )
        db.add(order)
        db.flush() 

        for items in order_items:
            items.order_id = order.id
            db.add(items)
        
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
        
        db.commit()
        db.refresh(order)

        items = (
            db.query(
                models.OrderItem.id,
                models.OrderItem.product_id,
                models.OrderItem.product_name,
                models.OrderItem.product_price,
                models.OrderItem.quantity,
                models.Product.image_url
            )
            .join(models.Product, models.Product.id == models.OrderItem.product_id)
            .filter(models.OrderItem.order_id == order.id)
            .all()
        )

        return {
            "id": order.id,
            "status": order.status,
            "user_id": order.user_id,
            "total_amount": float(order.total_amount),
            "items": [
                {
                    "id": i.id,
                    "product_id": i.product_id,
                    "product_name": i.product_name,
                    "product_price": float(i.product_price),
                    "quantity": i.quantity,
                    "image_url": i.image_url
                }
                for i in items
            ]
        }

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order placement failed"
        )

@router.get("/")
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    orders = (
        db.query(models.Order)
        .filter(models.Order.user_id == current_user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )

    result = []

    for o in orders:
        items = (
            db.query(
                models.OrderItem.product_id,
                models.Product.name.label("product_name"),
                models.Product.price.label("price"),
                models.Product.image_url.label("image_url"),
                models.OrderItem.quantity,
            )
            .join(models.Product, models.Product.id == models.OrderItem.product_id)
            .filter(models.OrderItem.order_id == o.id)
            .all()
        )

        result.append({
            "id": o.id,
            "status": o.status,
            "total_amount": float(o.total_amount),
            "created_at": o.created_at,
            "items": [
                {
                    "product_id": i.product_id,
                    "product_name": i.product_name,
                    "price": float(i.price),
                    "quantity": i.quantity,
                    "image_url": i.image_url,
                }
                for i in items
            ]
        })

    return {"data": result}

@router.get("/{order_id}",response_model=OrderOut)
def get_my_order(order_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):

    orders = (
        db.query(models.Order).filter(
            models.Order.id == order_id,
            models.Order.user_id == current_user.id
        ).first()
    )
    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return {
            "id": orders.id,
            "user_id": orders.user_id,
            "status": orders.status,
            "total_amount": float(orders.total_amount),
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "product_price": float(item.product_price),
                    "quantity": item.quantity,
                    "image_url": item.product.image_url
                }
                for item in orders.items
            ]
        }

@router.get('/admin/orders', dependencies=[Depends(admin_required)])
def list_orders(status: Optional[OrderStatus] = None , db: Session = Depends(get_db)):
    query = db.query(models.Order)
    if status:
        query = query.filter(models.Order.status == status)

    orders = query.order_by(models.Order.created_at.desc()).all()

    result = []

    for o in orders:
        items = (
            db.query(
                models.OrderItem.product_id,
                models.Product.name.label("product_name"),
                models.Product.price.label("price"),
                models.Product.image_url.label("image_url"),
                models.OrderItem.quantity,
            )
            .join(models.Product, models.Product.id == models.OrderItem.product_id)
            .filter(models.OrderItem.order_id == o.id)
            .all()
        )

        result.append({
            "id": o.id,
            "status": o.status,
            "user_id" : o.user_id,
            "total_amount": float(o.total_amount),
            "created_at": o.created_at,
            "items": [
                {
                    "product_id": i.product_id,
                    "product_name": i.product_name,
                    "price": float(i.price),
                    "quantity": i.quantity,
                    "image_url": i.image_url,
                }
                for i in items
            ]
        })

    return {"data": result}

@router.patch("/admin/orders/{order_id}/status",response_model=OrderOut)
def update_order_status(order_id: int,payload: OrderUpdateStatus,db: Session = Depends(get_db),dependencies=[Depends(admin_required)]):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Order Not Found")
    
    allowed = ALLOWED_TRANSITIONS[order.status]

    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {order.status}"
        )
    
    order.status = payload.status
    db.commit()
    db.refresh(order)

    return order

@router.get("/admin/{order_id}")
def admin_get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    items = (
        db.query(
            models.OrderItem.id,
            models.OrderItem.quantity,
            models.Product.name.label("product_name"),
            models.Product.price.label("product_price"),
            models.Product.image_url.label("image_url"),
        )
        .join(models.Product, models.Product.id == models.OrderItem.product_id)
        .filter(models.OrderItem.order_id == order.id)
        .all()
    )


    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": float(order.total_amount),
        "items": [
            {
                "id": i.id,
                "product_name": i.product_name,
                "product_price": float(i.product_price),
                "quantity": i.quantity,
                "image_url": i.image_url
            }
            for i in items
        ]
    }

@router.post("/{order_id}/pay")
def pay_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if order.status !=  OrderStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order cannot be paid")

    order.status = OrderStatus.paid
    db.commit()

    return {"success": True}
@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.status != OrderStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be cancelled"
        )

    items = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == order.id
    ).all()

    for item in items:
        inventory = db.query(models.Inventory).filter(
            models.Inventory.product_id == item.product_id
        ).first()

        if inventory:
            inventory.quantity += item.quantity
            inventory.reserved_quantity -= item.quantity

            if inventory.reserved_quantity < 0:
                inventory.reserved_quantity = 0 

    order.status = "cancelled"

    db.commit()

    return {"success": True}
