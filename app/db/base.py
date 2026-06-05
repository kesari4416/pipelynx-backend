"""
Database base classes and shared types
This module prevents circular imports between db and models
"""
from sqlalchemy.orm import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()
