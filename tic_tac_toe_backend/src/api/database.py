import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


DB_PATH = os.getenv("TICTACTOE_DB_URL", "sqlite:///./tic_tac_toe.db")
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


# PUBLIC_INTERFACE
def get_db():
    """Dependency that provides a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
