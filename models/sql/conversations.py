from sqlmodel import SQLModel, Field
from ..enums import ConversationType


class ConversationBase(SQLModel):
    __tablename__ = "conversations"
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    contact_id: int = Field(foreign_key="contacts.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    type: ConversationType = Field(..., schema_extra={"examples": ["text"]})
    started_at: str = Field(default=None)


class Conversation(ConversationBase, table=True):
    __tablename__ = "conversations"
    id: int = Field(default=None, primary_key=True)