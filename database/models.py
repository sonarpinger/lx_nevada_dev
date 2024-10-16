from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# user has username and a list of environments
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)

    # Define the relationship to Environment
    # User can have many environments
    environments = relationship("Environment", back_populates="users")

    # totp 
    is_totp_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(50))


# environment has machine name, course and ip address
class Environment(Base):
    __tablename__ = 'environments'

    id = Column(Integer, primary_key=True, index=True)
    machine_name = Column(String(50), nullable=False)
    course = Column(String(50), nullable=False)
    vmid = Column(Integer, nullable=False)
    # can be defined later
    ip_address = Column(String(50))
    status = Column(String(50), default="undefined", nullable=False)
    
    # Define the relationship to User
    # Environment can only have one user
    users = relationship("User", back_populates="environments")
    user_id = Column(Integer, ForeignKey('users.id'))
    
