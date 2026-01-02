from typing import List
from fastapi import APIRouter, Depends, HTTPException,status
from .. schemas import CategoryOut,CategoryCreate
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
