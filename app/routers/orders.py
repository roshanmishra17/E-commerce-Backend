from typing import List
from sqlalchemy.orm import Session
from .. database import get_db
from . admin import admin_required
from fastapi import APIRouter, Depends, HTTPException,status
from .. import models
from .. oauth import get_current_active_user
from .. schemas import OrderOut
from sqlalchemy.exc import SQLAlchemyError


router = APIRouter(prefix='/orders',tags=['Orders'])


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

        return order
    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order placement failed"
        )

@router.get('/',response_model=List[OrderOut])
def list_my_orders(db: Session = Depends(get_db),current_user: models.User = Depends(get_current_active_user)):
    return(
        db.query(models.Order).filter(models.Order.user_id == current_user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )

@router.get('/{order_id}',response_model=OrderOut)
def get_my_order(order_id : int,db : Session = Depends(get_db),current_user: models.User = Depends(get_current_active_user)):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id,models.Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Order Not Found")
    
    return order