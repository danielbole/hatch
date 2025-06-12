from asyncio import sleep
from datetime import datetime
import httpx


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlmodel import select

from pydantic_extra_types.phone_numbers import PhoneNumber

from models.sql.messages import Message, MessageBase
from models.enums import Provider, TextMessageType, ConversationType
from models.messages import IncomingText, OutgoingText, IncomingEmail, OutgoingEmail
from models.sql.user import User
from models.sql.contacts import Contact
from models.sql.conversations import Conversation
from database import get_session

router = APIRouter(
    prefix="/messages",
    tags=["messages"]
)


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
    
    if message.conversation_id is not None:
        conversation = session.exec(
            select(Conversation).where(Conversation.id == message.conversation_id)
        ).first()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation does not exist")
        if conversation.type != conversation_type:
            raise HTTPException(status_code=400, detail="Conversation type mismatch")

    if conversation_type is ConversationType.text:
        source = session.exec(
            select(User.phone_number).where(
                (User.id == message.user_id)
            )
        ).first()
        destination = session.exec(
            select(Contact.phone_number).where(
                (Contact.id == message.contact_id)
            )
        ).first()
    elif conversation_type is ConversationType.email:
        source = session.exec(
            select(User.email_address).where(
                (User.id == message.user_id)
            )
        ).first()
        destination = session.exec(
            select(Contact.email_address).where(
                (Contact.id == message.contact_id)
            )
        ).first()
        
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
    
    if message.conversation_id is not None:
        if session.exec(
            select(Conversation.id).where(Conversation.id == message.conversation_id)
        ).first() is None:
            raise HTTPException(status_code=404, detail="Conversation does not exist")

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
            print(f"Message sent successfully: {response.json()}")

            if message.conversation_id is None:
                conversation = Conversation(
                    user_id=message.user_id,
                    contact_id=message.contact_id,
                    type=conversation_type,
                    started_at=datetime.utcnow()
                )
                session.add(conversation)
                session.commit()
                session.refresh(conversation)
                message.conversation_id = conversation.id
            
            db_message = Message.model_validate(message)
            session.add(db_message)
            session.commit()
            session.refresh(db_message)
            return [db_message, outgoing.dict(), response.json()]
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to send message: {response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {e}") from e

@router.post("/receive/text")
async def receive_text(incoming: IncomingText, session: Session = Depends(get_session)):
    
    user_id = session.exec(
        select(User.id).where(
            (User.phone_number == incoming.destination)
        )
    ).first()
    
    print(f"User ID: {user_id}")
    if user_id is None:
        raise HTTPException(status_code=404, detail=f"No user associated with destination {incoming.destination}")

    contact_id = session.exec(
        select(Contact.id).where(
            (Contact.phone_number == incoming.source)
        )
    ).first()
    
    print(f"Contact ID: {contact_id}")
    if contact_id is None:
        raise HTTPException(status_code=404, detail=f"No contact associated with source {incoming.source}")
    
    conversation_id = session.exec(
        select(Conversation.id).where(
            (Conversation.user_id == user_id) &
            (Conversation.contact_id == contact_id) &
            (Conversation.type == ConversationType.text)
        )
    ).first()
    
    if conversation_id is None:
        conversation = Conversation(user_id=user_id, contact_id=contact_id, type=ConversationType.text, started_at=datetime.utcnow())
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        conversation_id = conversation.id
    
    message = Message(
        user_id=user_id,
        contact_id=contact_id,
        conversation_id=conversation_id,
        message_type=incoming.type,
        content=incoming.body,
        attachment=incoming.attachment or [],
        timestamp=incoming.timestamp
    )
    
    session.add(message)
    session.commit()
    session.refresh(message)
    return {**incoming.dict()}

@router.post("/receive/email")
async def receive_email(incoming: IncomingEmail, session: Session = Depends(get_session)):
    
    user_id = session.exec(
        select(User.id).where(
            (User.email_address == incoming.destination)
        )
    ).first()
    
    if user_id is None:
        raise HTTPException(status_code=404, detail=f"No user associated with destination {incoming.destination}")

    contact_id = session.exec(
        select(Contact.id).where(
            (Contact.email_address == incoming.source)
        )
    ).first()
    
    if contact_id is None:
        raise HTTPException(status_code=404, detail=f"No contact associated with source {incoming.source}")

    conversation_id = session.exec(
        select(Conversation.id).where(
            (Conversation.user_id == user_id) &
            (Conversation.contact_id == contact_id) &
            (Conversation.type == ConversationType.email)
        )
    ).first()
    
    if conversation_id is None:
        conversation = Conversation(user_id=user_id, contact_id=contact_id, type=ConversationType.email, started_at=datetime.utcnow())
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        conversation_id = conversation.id

    message = Message(
        user_id=user_id,
        contact_id=contact_id,
        conversation_id=conversation_id,
        message_type=ConversationType.email,
        content=incoming.body,
        attachment=incoming.attachment or [],
        timestamp=incoming.timestamp
    )

    session.add(message)
    session.commit()
    session.refresh(message)
    return {**incoming.dict()}