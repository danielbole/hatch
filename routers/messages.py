from asyncio import sleep
from datetime import datetime, timezone
import httpx

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlmodel import select

from pydantic_extra_types.phone_numbers import PhoneNumber

from models.sql.messages import Message, MessageBase
from models.enums import Provider, TextMessageType, ConversationType
from models.messages import IncomingMessage, OutgoingText, OutgoingEmail
from models.sql.user import User
from models.sql.contacts import Contact
from models.sql.conversations import Conversation
from database import get_session

router = APIRouter(
    prefix="/messages",
    tags=["messages"]
)

def get_conversation(session: Session, user_id: int, contact_id: int, conversation_type: ConversationType):
    conversation = session.exec(
        select(Conversation).where(
            (Conversation.user_id == user_id) &
            (Conversation.contact_id == contact_id) &
            (Conversation.type == conversation_type)
        )
    ).first()
    return conversation if conversation else None

def get_user_phone_number(session: Session, user_id: int):
    phone_number = session.exec(
        select(User.phone_number).where(
            (User.id == user_id)
        )
    ).first()
    return phone_number if phone_number else None

def get_contact_phone_number(session: Session, contact_id: int):
    phone_number = session.exec(
        select(Contact.phone_number).where(
            (Contact.id == contact_id)
        )
    ).first()
    return phone_number if phone_number else None

def get_user_email_address(session: Session, user_id: int):
    email_address = session.exec(
        select(User.email_address).where(
            (User.id == user_id)
        )
    ).first()
    return email_address if email_address else None

def get_contact_email_address(session: Session, contact_id: int):
    email_address = session.exec(
        select(Contact.email_address).where(
            (Contact.id == contact_id)
        )
    ).first()
    return email_address if email_address else None

def get_user_id_by_phone(session: Session, phone_number: str):
    user_id = session.exec(
        select(User.id).where(
            (User.phone_number == phone_number)
        )
    ).first()
    return user_id if user_id else None

def get_contact_id_by_phone(session: Session, phone_number: str):
    contact_id = session.exec(
        select(Contact.id).where(
            (Contact.phone_number == phone_number)
        )
    ).first()
    return contact_id if contact_id else None

def get_user_id_by_email(session: Session, email_address: str):
    user_id = session.exec(
        select(User.id).where(
            (User.email_address == email_address)
        )
    ).first()
    return user_id if user_id else None

def get_contact_id_by_email(session: Session, email_address: str):
    contact_id = session.exec(
        select(Contact.id).where(
            (Contact.email_address == email_address)
        )
    ).first()
    return contact_id if contact_id else None

@router.post("/send")

async def send_message(message: MessageBase, session: Session = Depends(get_session)):
    source = None
    destination = None
    provider = None
    conversation_type = None
    outgoing = None
    
    if message.message_type in [TextMessageType.sms, TextMessageType.mms]:
        provider = Provider.text
        conversation_type = ConversationType.text
    elif message.message_type == ConversationType.email:
        provider = Provider.email
        conversation_type = ConversationType.email
    else:
        raise HTTPException(status_code=404, detail="Invalid message type")
    
    conversation = get_conversation(
        session, 
        message.user_id, 
        message.contact_id, 
        conversation_type
    )

    if message.conversation_id is not None:
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation id is incorrect or does not exist")
        if conversation.type != conversation_type:
            raise HTTPException(status_code=400, detail="Conversation type mismatch")

    if conversation_type is ConversationType.text:
        source = get_user_phone_number(session, message.user_id)
        destination = get_contact_phone_number(session, message.contact_id)
    elif conversation_type is ConversationType.email:
        source = get_user_email_address(session, message.user_id)
        destination = get_contact_email_address(session, message.contact_id)
        
    if source is None:
        raise HTTPException(status_code=404, detail="User does not exist")
    if destination is None:
        raise HTTPException(status_code=404, detail="Contact does not exist")

    if conversation_type is ConversationType.text:
        provider = Provider.text
    elif conversation_type is ConversationType.email:
        provider = Provider.email
        
    if provider is None:
        raise HTTPException(status_code=404, detail="Invalid message type or provider not found")

    if conversation_type is ConversationType.text:
        outgoing = OutgoingText(
            source=PhoneNumber(source),
            destination=PhoneNumber(destination),
            type=message.message_type,
            body=message.content,
            attachment=message.attachment or [],
        )
    elif conversation_type is ConversationType.email:
        outgoing = OutgoingEmail(
            source=source,
            destination=destination,
            body=message.content,
            attachment=message.attachment or [],
        )

    try:
        attempt = 0
        while attempt < 3:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        provider.value,
                        json=outgoing.model_dump(by_alias=True, exclude_none=True)
                    )
                    if response.status_code == 200:
                        break
                    else:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Failed to send message: {response.text}"
                        )
            except HTTPException as e:
                attempt = attempt + 1
                await sleep(0.25 * 2 ** attempt)
        
        if response.status_code == 200:
            if message.conversation_id is None and conversation is None:
                conversation = Conversation(
                    user_id=message.user_id,
                    contact_id=message.contact_id,
                    type=conversation_type,
                    started_at=datetime.now(timezone.utc)
                )
                session.add(conversation)
                session.commit()
                session.refresh(conversation)
                message.conversation_id = conversation.id
            
            db_message = Message.model_validate(message)
            session.add(db_message)
            session.commit()
            session.refresh(db_message)
            return [db_message, outgoing.model_dump(), response.json()]
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to send message: {response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e}") from e

@router.post("/receive")
async def receive(incoming: IncomingMessage, session: Session = Depends(get_session)):
    
    conversation_type = None
    message_type = None
    conversation_id = None

    if incoming.type not in [TextMessageType.sms, TextMessageType.mms]:
        user_id = get_user_id_by_email(session, incoming.destination)
        contact_id = get_contact_id_by_email(session, incoming.source)
        conversation_type = ConversationType.email
        message_type = ConversationType.email
    else:
        user_id = get_user_id_by_phone(session, incoming.destination)
        contact_id = get_contact_id_by_phone(session, incoming.source)
        conversation_type = ConversationType.text
        message_type = incoming.type


    if user_id is None:
        raise HTTPException(status_code=404, detail=f"No user associated with destination {incoming.destination}")
    if contact_id is None:
        raise HTTPException(status_code=404, detail=f"No contact associated with source {incoming.source}")
    
    conversation = get_conversation(
        session, 
        user_id, 
        contact_id, 
        conversation_type
    )
    
    if conversation is None:
        conversation = Conversation(user_id=user_id, contact_id=contact_id, type=ConversationType.text, started_at=datetime.utcnow())
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        conversation_id = conversation.id
    else:
        conversation_id = conversation.id
    
    message = Message(
        user_id=user_id,
        contact_id=contact_id,
        conversation_id=conversation_id,
        message_type=message_type,
        content=incoming.body,
        attachment=incoming.attachment or [],
        timestamp=incoming.timestamp
    )
    
    session.add(message)
    session.commit()
    session.refresh(message)
    return {**incoming.dict()}

