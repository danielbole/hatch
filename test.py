import httpx
import json

import psycopg2

drop_tables = """
DO $$ DECLARE
    r RECORD;
BEGIN
    -- if the schema you operate on is not "current", you will want to
    -- replace current_schema() in query with 'schematodeletetablesfrom'
    -- *and* update the generate 'DROP...' accordingly.
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
"""
# Connect to the database
conn_params = {
    'host': 'localhost',
    'database': 'hatch',
    'user': 'user',
    'password': 'password'
}

try:
    # Establish a connection
    conn = psycopg2.connect(**conn_params)

    # Create a cursor object
    cur = conn.cursor()

    # Execute a query
    cur.execute(drop_tables)
    
    # Close the cursor and connection
    cur.close()
    conn.commit()
    print("All tables dropped successfully.")
    conn.close()

except psycopg2.Error as e:
    print(f"Error connecting to or querying the database: {e}")


user_url = "http://127.0.0.1:8000/users/"
contacts_url = "http://127.0.0.1:8000/contacts/"
recive_url = 'http://127.0.0.1:8000/messages/receive'
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
