"""SQLModel database table definitions."""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SAEnum, Text, Float
from src.utils.enums import Priority, Category


class Customer(SQLModel, table=True):
    """Customer table model."""

    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, nullable=False, max_length=255)
    name: str = Field(nullable=False, max_length=255)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class Ticket(SQLModel, table=True):
    """Ticket table model."""

    __tablename__ = "tickets"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id", nullable=False)
    raw_content: str = Field(sa_column=Column(Text, nullable=False))
    summary: str = Field(sa_column=Column(Text, nullable=False))

    category: Category = Field(
        sa_column=Column(SAEnum(Category, name="category_enum"), nullable=False)
    )

    priority: Priority = Field(
        sa_column=Column(SAEnum(Priority, name="priority_enum"), nullable=False)
    )

    sentiment_score: float = Field(
        sa_column=Column(Float, nullable=False)
    )

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
