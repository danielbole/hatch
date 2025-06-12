import httpx

recive_url = 'http://127.0.0.1:8000/api/messages/receive'

r = httpx.post(recive_url, data={
    "from": "+18045551234",
    "to": "+12016661234",
    "type": "sms",
    "messaging_provider_id": "message-1",
    "body": "text message",
    "attachments": None,
    "timestamp": "2024-11-01T14:00:00Z"
})

print(r.status_code)
print(r.json())