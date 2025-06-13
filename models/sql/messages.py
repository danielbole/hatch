from datetime import datetime
from typing import List
from sqlmodel import Field, SQLModel, Column
from sqlalchemy.dialects.postgresql import JSON
from ..enums import MessageType

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