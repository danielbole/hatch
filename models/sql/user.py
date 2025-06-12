from sqlmodel import SQLModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic import EmailStr


class UserBase(SQLModel):
    __tablename__ = "users"
    name: str = Field(schema_extra={"examples": ["Jane Doe"]})
    phone_number: PhoneNumber = Field(unique=True, schema_extra={"examples": ["+12016661234"]})
    email_address: EmailStr = Field(unique=True, schema_extra={"examples": ["jane.doe@example.com"]})


class User(UserBase, table=True):
    __tablename__ = "users"
    id: int = Field(default=None, primary_key=True)
