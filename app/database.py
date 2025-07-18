from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# For SQLite, the database will be a single file named 'memorybank.db' in the root directory.
SQLALCHEMY_DATABASE_URL = "sqlite:///./memorybank.db"

# The engine is the entry point to the database.
# The 'connect_args' is needed only for SQLite to allow multithreaded access.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Each instance of the SessionLocal class will be a database session.
# The class itself is not a session yet, but will create one when instantiated.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from this class to create each of the ORM models.
Base = declarative_base()