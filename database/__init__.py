from sqlalchemy import *
from sqlalchemy.orm import create_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .models import User, Environment, Base
from .schemas import *
  
engine = create_engine("mysql+pymysql://USRNAME:PASSWD127.0.0.1:3306/lx",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
)

#reset the database
# Base.metadata.drop_all(engine)

# Create the tables
Base.metadata.create_all(engine)

# # Create a Session
Session = sessionmaker(bind=engine, autocommit=False)
def get_session():
    while True:
        try:
            session = Session()
            yield session
            session.commit()
            break
        except Exception as e:
            print(f"Error: {e}")
            session.rollback()
        finally:
            session.close()
