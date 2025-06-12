from asyncio import sleep
from datetime import datetime
from enum import Enum
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException

import httpx
from pydantic import EmailStr, BaseModel, AliasChoices
from pydantic import Field as PydanticField
from pydantic_extra_types.phone_numbers import PhoneNumber

from sqlalchemy.dialects.postgresql import JSON

from sqlmodel import SQLModel, Field, create_engine, Session, Column, select

DATABASE_URL = "postgresql://user:password@localhost:5432/hatch"

# class Provider(str, Enum):
#     email = "https://www.mailplus.app/api/email"
#     text = "https://www.provider.app/api/messages"
    
class Provider(str, Enum):
    email = "http://127.0.0.1:8000/api/test/messages/receive"
    text = "http://127.0.0.1:8000/api/test/messages/receive"

class TextMessageType(str, Enum):
    sms = "sms"
    mms = "mms"
    
class MessageType(str, Enum):
    sms = "sms"
    mms = "mms"
    email = "email"
    
class ConversationType(str, Enum):
    text = "text"
    email = "email"

class IncomingText(BaseModel):
    source: PhoneNumber | EmailStr = PydanticField(alias="from", example="+18045551234")
    destination: PhoneNumber | EmailStr = PydanticField(alias="to", example="+12016661234")
    type: TextMessageType = PydanticField(..., example="sms", description="Type of text message (sms, mms)")
    messageProviderID: str = PydanticField(..., example="message-1", validation_alias=AliasChoices("messaging_provider_id", "xillio_id"))
    body: str = PydanticField(..., example="text message")
    attachment: Optional[List[str]] = PydanticField(None, example="null")
    timestamp: datetime = PydanticField(..., example="2024-11-01T14:00:00Z")
    
class OutgoingText(BaseModel):
    source: PhoneNumber | EmailStr = PydanticField(serialization_alias="from", example="+12016661234")
    destination: PhoneNumber | EmailStr = PydanticField(serialization_alias="to", example="+18045551234")
    type: TextMessageType = PydanticField(..., example="sms", description="Type of text message (sms, mms)")
    body: str = PydanticField(..., example="text message")
    attachment: Optional[List[str]] = PydanticField(None, example="null")
    
    class Config:
        allow_population_by_field_name = True

class IncomingEmail(BaseModel):
    source: PhoneNumber | EmailStr = PydanticField(alias="from", example="john.smith@example.com")
    destination: PhoneNumber | EmailStr = PydanticField(alias="to", example="jane.doe@example.com")
    messageProviderID: str = PydanticField(..., validation_alias=AliasChoices("messaging_provider_id", "xillio_id"))
    body: str = PydanticField(..., example="text message")
    attachment: Optional[List[str]] = PydanticField(None, example="null")
    timestamp: datetime = PydanticField(..., example="2024-11-01T14:00:00Z")
    
class OutgoingEmail(BaseModel):
    source: PhoneNumber | EmailStr = PydanticField(serialization_alias="from", example="jane.doe@example.com")
    destination: PhoneNumber | EmailStr = PydanticField(serialization_alias="to", example="john.smith@example.com")
    body: str = PydanticField(..., example="text message")
    attachment: Optional[List[str]] = PydanticField(None, example="null")
    
    class Config:
        allow_population_by_field_name = True

class UserBase(SQLModel):
    __tablename__ = "users"
    name: str = Field(schema_extra={"examples": ["Jane Doe"]})
    phone_number: PhoneNumber = Field(unique=True, schema_extra={"examples": ["+12016661234"]})
    email_address: EmailStr = Field(unique=True, schema_extra={"examples": ["jane.doe@example.com"]})

class User(UserBase, table=True):
    __tablename__ = "users"
    id: int = Field(default=None, primary_key=True)

class ContactBase(SQLModel):
    __tablename__ = "contacts"
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    name: str = Field(schema_extra={"examples": ["John Smith"]})
    phone_number: PhoneNumber = Field(default=None, schema_extra={"examples": ["+18045551234"]})
    email_address: EmailStr = Field(default=None, schema_extra={"examples": ["john.smith@example.com"]})

class Contact(ContactBase, table=True):
    __tablename__ = "contacts"
    id: int = Field(default=None, primary_key=True)

class ConversationBase(SQLModel):
    __tablename__ = "conversations"
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    contact_id: int = Field(foreign_key="contacts.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    type: ConversationType = Field(..., schema_extra={"examples": ["text"]})
    started_at: str = Field(default=None)

class Conversation(ConversationBase, table=True):
    __tablename__ = "conversations"
    id: int = Field(default=None, primary_key=True)

class MessageBase(SQLModel):
    __tablename__ = "messages"
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    contact_id: int = Field(foreign_key="contacts.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    conversation_id: int | None = Field(default=None, foreign_key="conversations.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    message_type: MessageType = Field(MessageType.sms, schema_extra={"examples": [MessageType.sms]})
    content: str = Field(..., schema_extra={"examples": ["Hello, This is a message!"]})
    attachment: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    timestamp: datetime = Field(..., schema_extra={"examples": [datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")]})

class Message(MessageBase, table=True):
    __tablename__ = "messages"
    id: int = Field(default=None, primary_key=True)

async def get_session():
    engine = create_engine(DATABASE_URL, echo=True)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

app = FastAPI()

@app.put("/api/users", tags=["Users"])
async def create_user(user: UserBase, session: Session = Depends(get_session)):
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get("/api/users", tags=["Users"])
async def read_user(session: Session = Depends(get_session)):
    user = session.exec(select(User)).all()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return user

@app.put("/api/contacts", tags=["Contacts"])
async def create_contact(contact: ContactBase, session: Session = Depends(get_session)):
    db_contact = Contact.model_validate(contact)
    session.add(db_contact)
    session.commit()
    session.refresh(db_contact)
    return db_contact

@app.get("/api/contacts", tags=["Contacts"])
async def read_contacts(session: Session = Depends(get_session)):
    contacts = session.exec(select(Contact)).all()
    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found")
    return contacts

@app.get("/api/messages/{message_id}", tags=["Messages"])
async def read_messages(message_id: int):
    return {"message_id": message_id, "content": "Hello, World!"}

@app.get("/api/messages/{user_id}/messages/{message_id}", tags=["Messages"])
async def read_user_messages(user_id: int, message_id: int):
    return {"user_id": user_id, "message_id": message_id, "content": "Hello, User!"}

@app.post("/api/messages", tags=["Messages"])
async def create_message(message: MessageBase, session: Session = Depends(get_session)):
    db_message = Message.model_validate(message)
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message

@app.post("/api/messages/send", tags=["Messages"])
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

@app.post("/api/messages/receive/text", tags=["Messages"])
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

@app.post("/api/messages/receive/email", tags=["Messages"])
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

request_count = 0

@app.post("/api/test/messages/receive", tags=["Messages"])
async def test_receive_message(json: dict):
    # global request_count
    # request_count += 1
    # if request_count < 4:
    #     raise HTTPException(status_code=429, detail=f"Too many requests, please try again later. {request_count}")
    return {"status": "success", "message": "Message received successfully", "data": json}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)