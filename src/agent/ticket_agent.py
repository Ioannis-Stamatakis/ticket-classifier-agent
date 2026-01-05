"""Ticket classification agent using PydanticAI and Google Gemini."""
import os
import asyncpg
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from src.models.schemas import ProcessedTicket


def create_ticket_agent(api_key: str) -> Agent[asyncpg.Pool, ProcessedTicket]:
    """
    Create and configure the ticket classification agent.

    Args:
        api_key: Google Gemini API key

    Returns:
        Configured PydanticAI agent
    """
    # Set the API key as an environment variable (required by GoogleModel)
    os.environ['GOOGLE_API_KEY'] = api_key

    # Initialize Google Gemini model (uses GOOGLE_API_KEY environment variable)
    model = GoogleModel('gemini-2.5-flash')

    # Create agent with dependency injection and structured output
    agent = Agent(
        model=model,
        deps_type=asyncpg.Pool,
        output_type=ProcessedTicket,
        system_prompt="""You are an expert customer support ticket analyzer.

Your task is to analyze customer support tickets and extract the following information:

1. **Summary**: Create a concise 1-2 sentence summary of the ticket's main issue or request.

2. **Category**: Classify the ticket into one of these categories:
   - billing: Issues related to payments, charges, refunds, or subscriptions
   - technical: Technical problems, bugs, errors, or system issues
   - feature_request: Requests for new features or improvements
   - general: General inquiries, questions, or uncategorized issues

3. **Priority**: Determine the urgency level:
   - low: Minor issues, questions, general feedback
   - medium: Important but not urgent, workarounds available
   - high: Significant issues affecting user experience
   - critical: Urgent issues requiring immediate attention, blocking functionality

4. **Sentiment Score**: Analyze the emotional tone from 0.0 (very negative, angry, frustrated)
   to 1.0 (very positive, happy, satisfied). Consider:
   - Language used (polite vs aggressive)
   - Emotional indicators (exclamation marks, capitalization)
   - Overall tone and context

Analyze the ticket carefully and provide accurate, well-reasoned classifications."""
    )

    return agent
