from enum import Enum

# class Provider(str, Enum):
#     email = "https://www.mailplus.app/api/email"
#     text = "https://www.provider.app/api/messages"

class Provider(str, Enum):
    email = "http://127.0.0.1:8000/test/messages/receive"
    text = "http://127.0.0.1:8000/test/messages/receive"

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