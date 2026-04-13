import math
from fastapi import APIRouter, Depends, HTTPException, Query,status
from .. schemas import CategoryOut, ProductCreate, ProductListResponse, ProductOut, ProductUpdate
from sqlalchemy.orm import Session
from .. database import get_db
from . admin import admin_required
from .. import models



router = APIRouter(tags=['Products'],prefix='/products')

@router.post('/',response_model=ProductOut,status_code=status.HTTP_201_CREATED,dependencies=[Depends(admin_required)])
def create_products(payload : ProductCreate,db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == payload.category_id).first()
    
    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or inactive category"
        )

    products = models.Product(**payload.dict())

    db.add(products)
    db.commit()
    db.refresh(products)

    return products

@router.get('/',response_model=ProductListResponse)
def get_all_product(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    category_id: int | None = Query(None),
    search: str | None = Query(None),
    sort: str | None = Query(None),
    db: Session = Depends(get_db),
):
    base_query = db.query(models.Product).filter(models.Product.is_active == True)

    if category_id:
        base_query = base_query.filter(models.Product.category_id == category_id)
    
    if search:
        base_query = base_query.filter(
            models.Product.name.ilike(f"%{search}%")
        )

    if sort == "price_asc":
        base_query = base_query.order_by(models.Product.price.asc())
    elif sort == "price_desc":
        base_query = base_query.order_by(models.Product.price.desc())

    total_items = base_query.count()

    offset = (page - 1) * limit
    products = base_query.offset(offset).limit(limit).all()

    total_pages = math.ceil(total_items / limit) if total_items else 1

    return {
        "data": products,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages
        }
    }
@router.get('/{product_id}', response_model=ProductOut)
def get_product(product_id : int, db: Session = Depends(get_db)):

    product = db.query(models.Product).filter(models.Product.id == product_id).first()

    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product

@router.get("/slug/{slug}", response_model=ProductOut)
def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.slug == slug,models.Product.is_active == True).first()
    if not product or not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.patch('/{product_id}',response_model=ProductOut,dependencies=[Depends(admin_required)])
def update_product(product_id : int,payload : ProductUpdate,db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product

@router.patch('/{product_id}/deactivate',response_model=ProductOut,dependencies=[Depends(admin_required)])
def deactivate_product(product_id : int,db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False

    db.commit()
    db.refresh(product)
    return product

@router.patch('/{product_id}/activate',response_model=ProductOut,dependencies=[Depends(admin_required)])
def activate_product(product_id : int,db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category = db.query(models.Category).filter(models.Category.id == product.category_id).first()

    if not category or not category.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot activate product in inactive category"
        )

    product.is_active = True

    db.commit()
    db.refresh(product)
    return product
