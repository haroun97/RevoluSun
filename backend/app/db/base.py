"""
SQLAlchemy declarative base for all database models.

Every table model (ImportBatch, RawMeterReading, etc.) inherits from Base
so SQLAlchemy can create tables and map rows to Python objects.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models; subclasses define table name and columns."""
    pass
