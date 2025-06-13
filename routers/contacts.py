from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlmodel import select
from models.sql.contacts import Contact, ContactBase
from database import get_session

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"]
)


@router.put("/")
async def create_contact(contact: ContactBase, session: Session = Depends(get_session)):
    db_contact = Contact.model_validate(contact)
    session.add(db_contact)
    session.commit()
    session.refresh(db_contact)
    return db_contact

@router.get("/")
async def read_contacts(session: Session = Depends(get_session)):
    contacts = session.exec(select(Contact)).all()
    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found")
    return contacts