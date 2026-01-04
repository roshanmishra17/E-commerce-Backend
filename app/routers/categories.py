from typing import List
from fastapi import APIRouter, Depends, HTTPException,status
from .. schemas import CategoryOut,CategoryCreate, CategoryUpdate
from . admin import admin_required
from sqlalchemy.orm import Session
from .. database import get_db
from .. import models


router = APIRouter(
    prefix="/categories",
    tags=['Category']
)

@router.post('/',response_model=CategoryOut,status_code=status.HTTP_201_CREATED)
def create_category(payload : CategoryCreate,db: Session = Depends(get_db),dependencies=[Depends(admin_required)]):
    name = payload.name.strip().lower()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name cannot be empty"
        )
    existing = (
        db.query(models.Category)
        .filter(models.Category.name == name)
        .first()
    )

    if existing :
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category already exists"
        )
    
    category = models.Category(name = name)

    db.add(category)
    db.commit()
    db.refresh(category)

    return category

@router.get('/',response_model=List[CategoryOut])
def get_categories(db : Session = Depends(get_db)):
    return db.query(models.Category).all()

@router.patch('/{category_id}',response_model=CategoryOut)
def update_category(
    category_id : int,
    payload : CategoryUpdate,
    db: Session = Depends(get_db),
    dependencies=[Depends(admin_required)]
):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    name = payload.name.strip().lower()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name cannot be empty"
        )

    category.name = name

    db.commit()
    db.refresh(category)
    return category

@router.patch("/{category_id}/deactivate", response_model=CategoryOut)
def deactivate_category(
    category_id: int,
    db: Session = Depends(get_db),
    dependencies=[Depends(admin_required)]
):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    category.is_active = False
    db.commit()
    db.refresh(category)
    return category

@router.patch("/{category_id}/activate", response_model=CategoryOut)
def deactivate_category(
    category_id: int,
    db: Session = Depends(get_db),
    dependencies=[Depends(admin_required)]
):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    category.is_active = True
    db.commit()
    db.refresh(category)
    return category
