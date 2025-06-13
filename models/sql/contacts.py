from sqlmodel import SQLModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic import EmailStr


class ContactBase(SQLModel):
    __tablename__ = "contacts"
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE", schema_extra={"examples": [1]})
    name: str = Field(schema_extra={"examples": ["John Smith"]})
    phone_number: PhoneNumber = Field(default=None, schema_extra={"examples": ["+18045551234"]})
    email_address: EmailStr = Field(default=None, schema_extra={"examples": ["john.smith@example.com"]})


class Contact(ContactBase, table=True):
    __tablename__ = "contacts"
    id: int = Field(default=None, primary_key=True)