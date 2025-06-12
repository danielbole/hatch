from datetime import datetime
from typing import Optional, List

from pydantic_extra_types.phone_numbers import PhoneNumber
from pydantic import EmailStr, BaseModel, AliasChoices
from pydantic import Field as PydanticField

from models.enums import Provider, TextMessageType, ConversationType, MessageType

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