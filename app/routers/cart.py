from fastapi import APIRouter, Depends, HTTPException,status
from .. schemas import CartItemUpdate, CartOut
from .. oauth import get_current_active_user
from .. import models
from .. database import get_db
from sqlalchemy.orm import Session
from .. schemas import CartItemAdd



router = APIRouter(prefix='/cart',tags=['Cart'])

@router.post('/',response_model=CartOut)
def add_to_cart(payload :CartItemAdd , db: Session = Depends(get_db),current_user: models.User = Depends(get_current_active_user)):
    cart =  db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        cart = models.Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    inventory = db.query(models.Inventory).filter(models.Inventory.product_id == payload.product_id).first()
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Inventory Not Found")
    
    available = inventory.quantity - inventory.reserved_quantity
    if payload.quantity > available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
    
    item = db.query(models.CartItem).filter(models.CartItem.cart_id== cart.id,models.CartItem.product_id == payload.product_id).first()
    inventory.reserved_quantity += payload.quantity
    if item:
        item.quantity += payload.quantity
    else:
        item = models.CartItem(
            cart_id=cart.id,
            product_id=payload.product_id,
            quantity=payload.quantity
        )
        db.add(item)

    db.commit()
    db.refresh(cart)
    items = (
        db.query(
            models.CartItem.product_id,
            models.Product.name.label("product_name"),
            models.Product.price.label("price"),
            models.CartItem.quantity
        )
        .join(models.Product, models.Product.id == models.CartItem.product_id)
        .filter(models.CartItem.cart_id == cart.id)
        .all()
    )

    return {
        "id": cart.id,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product_name,
                "price": float(i.price),
                "quantity": i.quantity
            }
            for i in items
        ]
    }


@router.delete('/{product_id}', response_model=CartOut)
def remove_from_cart(product_id: int, db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_active_user)):

    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart Not Found")

    item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == cart.id,
        models.CartItem.product_id == product_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item Not Found")

    inventory = db.query(models.Inventory).filter(
        models.Inventory.product_id == product_id
    ).first()

    if inventory:
        inventory.reserved_quantity = max(0,inventory.reserved_quantity - item.quantity)


    db.delete(item)

    db.commit()

    items = (
        db.query(
            models.CartItem.product_id,
            models.Product.name.label("product_name"),
            models.Product.price.label("price"),
            models.CartItem.quantity
        )
        .join(models.Product, models.Product.id == models.CartItem.product_id)
        .filter(models.CartItem.cart_id == cart.id)
        .all()
    )

    return {
        "id": cart.id,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product_name,
                "price": float(i.price),
                "quantity": i.quantity
            }
            for i in items
        ]
    }


@router.get('/', response_model=CartOut)
def get_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    cart = (
        db.query(models.Cart)
        .filter(models.Cart.user_id == current_user.id)
        .first()
    )

    if not cart:
        return {"id": None, "items": []}

    items = (
        db.query(
            models.CartItem.product_id,
            models.Product.name.label("product_name"),
            models.Product.price.label("price"),
            models.Product.image_url.label("image_url"),

            models.CartItem.quantity
        )
        .join(models.Product, models.Product.id == models.CartItem.product_id)
        .filter(models.CartItem.cart_id == cart.id)
        .all()
    )

    return {
        "id": cart.id,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product_name,
                "price": float(i.price),
                "image_url": i.image_url,
                "quantity": i.quantity
            }
            for i in items
        ]
    }


@router.patch('/items/{product_id}',response_model=CartOut)
def update_cart(product_id : int,payload : CartItemUpdate,db : Session = Depends(get_db),current_user: models.User = Depends(get_current_active_user)):
    cart =  db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Cart Not Found")
    
    item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id,models.CartItem.product_id == product_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Item Not Found")
    
    inventory = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Inventory Not Found")
    
    old_quantity = item.quantity
    new_quantity = payload.quantity
    delta = new_quantity-old_quantity
    if delta > 0:
        availble = inventory.quantity - inventory.reserved_quantity
        if delta > availble:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Insufficient stock")
        inventory.reserved_quantity+=delta
    elif delta < 0:
        inventory.reserved_quantity = max(
            0,
            inventory.reserved_quantity + delta
        )

    item.quantity = new_quantity

    db.commit()
    db.refresh(cart)
    items = (
        db.query(
            models.CartItem.product_id,
            models.Product.name.label("product_name"),
            models.Product.price.label("price"),
            models.CartItem.quantity
        )
        .join(models.Product, models.Product.id == models.CartItem.product_id)
        .filter(models.CartItem.cart_id == cart.id)
        .all()
    )

    return {
        "id": cart.id,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product_name,
                "price": float(i.price),
                "quantity": i.quantity
            }
            for i in items
        ]
    }



