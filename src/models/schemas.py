"""Pydantic schemas for ticket processing."""
from pydantic import BaseModel, Field
from src.utils.enums import Priority, Category


class ProcessedTicket(BaseModel):
    """Structured output from ticket analysis agent."""

    summary: str = Field(
        description="Concise 1-2 sentence summary of the ticket"
    )

    category: Category = Field(
        description="Ticket category: billing, technical, feature_request, or general"
    )

    priority: Priority = Field(
        description="Ticket priority: low, medium, high, or critical"
    )

    sentiment_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Sentiment score from 0.0 (very negative) to 1.0 (very positive)"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
