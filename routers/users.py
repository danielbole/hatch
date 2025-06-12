from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlmodel import select
from models.sql.user import User, UserBase
from database import get_session

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.put("/")
async def create_user(user: UserBase, session: Session = Depends(get_session)):
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get("/")
async def read_user(session: Session = Depends(get_session)):
    user = session.exec(select(User)).all()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return user