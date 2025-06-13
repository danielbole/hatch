from fastapi import FastAPI

from routers import users, contacts, messages, test


app = FastAPI()

app.include_router(users.router)
app.include_router(contacts.router)
app.include_router(messages.router)
app.include_router(test.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)