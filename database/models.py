from sqlalchemy import (
    Column, ForeignKey, Integer, String, Boolean, DateTime, Float, Table, Enum
)
from sqlalchemy.types import Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

STATUS_ENUM = ('undefined', 'started', 'stopped', 'deleted', 'error')
USER_TYPE_ENUM = ('student', 'instructor', 'admin')

Base = declarative_base()

def utcnow():
    return datetime.datetime.now(tz=datetime.timezone.utc)

user_courses = Table(
    'user_courses',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id', ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
    user_type = Column(Enum(*USER_TYPE_ENUM), default='student', nullable=False)
    totp_secret = Column(String(50), nullable=True)
    is_totp_enabled = Column(Boolean, default=True)
    is_totp_confirmed = Column(Boolean, default=False)

    # Relationships
    environments = relationship(
        "Environment",
        back_populates="users",
        cascade="all, delete-orphan"
    )
    courses = relationship(
        "Course",
        secondary=user_courses,
        back_populates="users"
    )

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)

    instructors = relationship(
        "User",
        secondary=user_courses,
        back_populates="courses"
    )

    # Relationships
    users = relationship(
        "User",
        secondary=user_courses,
        back_populates="courses"
    )
    environments = relationship("Environment", back_populates="course")

# environment has machine name, course and ip address
class Environment(Base):
    __tablename__ = 'environments'

    id = Column(Integer, primary_key=True, index=True)
    machine_name = Column(String(50), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'))
    vmid = Column(Integer, nullable=False)
    # can be defined later
    ip_address = Column(String(50))
    status = Column(Enum(*STATUS_ENUM), default='undefined', nullable=False)

    # Define the relationship to User
    # Environment can only have one user
    users = relationship("User", back_populates="environments")
    user_id = Column(Integer, ForeignKey('users.id'))

class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, index=True)
    common_name = Column(String(50), nullable=False)
    connection_string = Column(String(255), nullable=False)
    environment_id = Column(Integer, ForeignKey('environments.id'))
    environment = relationship("Environment", back_populates="services")
