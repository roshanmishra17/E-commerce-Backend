from fastapi import APIRouter
from .. schemas import InventoryCreate, InventoryOut, InventoryUpdate
from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from .. database import get_db
from . admin import admin_required
from .. import models


router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.post('/',response_model=InventoryOut,status_code=status.HTTP_201_CREATED,dependencies=[Depends(admin_required)])
def create_inventory(payload : InventoryCreate,db : Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    inventory = db.query(models.Inventory).filter(models.Inventory.product_id == payload.product_id)
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already exists for this product"
        )
    
    inventory = models.Inventory(
        product_id=payload.product_id,
        quantity=payload.quantity
    )

    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory

@router.get('/{product_id}',response_model=InventoryOut,dependencies=[Depends(admin_required)])
def get_inventory(product_id : int,db : Session = Depends(get_db)):
    inventory = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found"
        )

    return inventory

@router.patch('/{product_id}',response_model=InventoryOut,dependencies=[Depends(admin_required)])
def update_product(product_id: int,payload: InventoryUpdate,db : Session = Depends(get_db)):
    inventory = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found"
        )
    if payload.quantity < inventory.reserved_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity cannot be less than reserved quantity"
        )

    inventory.quantity = payload.quantity
    db.commit()
    db.refresh(inventory)
    return inventory