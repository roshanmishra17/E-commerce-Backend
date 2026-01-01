from fastapi import APIRouter, Depends, HTTPException,status
from .. schemas import UserCreate, UserOut, UserUpdate
from .. import models
from .. database import get_db
from sqlalchemy.orm import Session
from .. utils import hash_pass
from .. oauth import get_current_active_user, get_current_user

router = APIRouter(
    prefix="/users",
    tags=['User']
)


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    hashed_password = hash_pass(user.password)

    new_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role=models.UserRole.customer
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@router.patch("/me", response_model=UserOut)
def update_current_user(
    user_update: UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if user_update.name is not None:
        current_user.name = user_update.name

    if user_update.password is not None:
        current_user.hashed_password = hash_pass(user_update.password)

    db.commit()
    db.refresh(current_user)

    return current_user
