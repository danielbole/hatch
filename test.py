import httpx
import json

user_url = "http://127.0.0.1:8000/users/"
contacts_url = "http://127.0.0.1:8000/contacts/"
recive_url = 'http://127.0.0.1:8000/messages/receive/text'
send_url = 'http://127.0.0.1:8000/messages/send'

users = []
contacts = []
# Create users
r = httpx.put(user_url, json={
    "name": "Jane Doe",
    "phone_number": "+12016661234",
    "email_address": "jane.doe@example.com"
})

assert r.status_code == 200, "Failed to create user"
users.append(r.json())

r = httpx.put(user_url, json={
    "name": "Anna",
    "phone_number": "+12016661235",
    "email_address": "anna@example.com"
})

assert r.status_code == 200, "Failed to create user"
users.append(r.json())

r = httpx.get(user_url)

assert r.status_code == 200, "Failed to retrieve users"
assert r.json() == users, "Users do not match"

# Create contacts
r = httpx.put(contacts_url, json={
    "user_id": 1,
    "name": "John Smith",
    "phone_number": "+18045551234",
    "email_address": "john.smith@example.com"
})
assert r.status_code == 200, "Failed to create contact"
contacts.append(r.json())
r = httpx.put(contacts_url, json={
    "user_id": 2,
    "name": "Elsa",
    "phone_number": "+18045551235",
    "email_address": "elsa@example.com"
})
assert r.status_code == 200, "Failed to create contact"
contacts.append(r.json())
r = httpx.get(contacts_url)
assert r.status_code == 200, "Failed to retrieve contacts"
assert contacts == r.json(), "Contacts do not match"

r = httpx.post(send_url, json={
    "user_id": 2,
    "contact_id": 2,
    "conversation_id": 1,
    "message_type": "sms",
    "content": "Do you want to build a snowman?",
    "attachment": [
        "string"
    ],
    "timestamp": "2025-06-13T15:31:51Z"
})

assert r.status_code != 200, "Conversation should not exist and should fail"

r = httpx.post(send_url, json={
    "user_id": 2,
    "contact_id": 2,
    "message_type": "sms",
    "content": "Do you want to build a snowman?",
    "attachment": [
        "string"
    ],
    "timestamp": "2025-06-13T15:31:51Z"
})

assert r.status_code == 200, "Failed to send message"

r = httpx.post(recive_url, data=json.dumps({
    "from": "+18045551234",
    "to": "+12016661234",
    "type": "sms",
    "messaging_provider_id": "message-1",
    "body": "text message",
    "attachment": None,
    "timestamp": "2024-11-01T14:00:00Z"
}))

assert r.status_code == 200, "Failed to receive message"
