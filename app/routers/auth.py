from fastapi import APIRouter, Depends, HTTPException,status
from fastapi.security import OAuth2PasswordRequestForm
from .. schemas import Token
from .. import models
from .. database import get_db
from sqlalchemy.orm import Session
from .. import utils
from .. oauth import create_access_token


router = APIRouter(tags=['Login'])

@router.post('/login',response_model=Token)
def login(userCred : OAuth2PasswordRequestForm = Depends(),db : Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == userCred.username).first()
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )

    if not user :
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail='Invalid Credentials')
    
    if not utils.verify(userCred.password,user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail='Invalid Credentials')
    
    access_token = create_access_token(data = {"user_id" : user.id , "role" : user.role.value})
    return {"access_token" : access_token, "token_type" : "bearer"}