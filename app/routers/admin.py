from fastapi import APIRouter, Depends, HTTPException,status
from oauth import get_current_user

router = APIRouter()

def admin_required(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user