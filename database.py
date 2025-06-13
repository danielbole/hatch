from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://user:password@localhost:5432/hatch"

async def get_session():
    engine = create_engine(DATABASE_URL, echo=True)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session