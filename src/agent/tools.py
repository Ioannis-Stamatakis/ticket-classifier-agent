"""Agent tools for ticket processing."""
import asyncpg
from pydantic_ai import RunContext


async def register_tools(agent):
    """Register tools with the ticket agent."""

    @agent.tool
    async def save_ticket(
        ctx: RunContext[asyncpg.Pool],
        customer_email: str,
        customer_name: str,
        raw_content: str,
        summary: str,
        category: str,
        priority: str,
        sentiment_score: float
    ) -> str:
        """
        Save customer information and ticket to the database.

        This tool performs an UPSERT on the customer (insert or update by email)
        and inserts a new ticket with the analyzed information.

        Args:
            ctx: RunContext containing the database pool
            customer_email: Customer's email address
            customer_name: Customer's full name
            raw_content: Original ticket content
            summary: Analyzed summary of the ticket
            category: Ticket category (billing/technical/feature_request/general)
            priority: Ticket priority (low/medium/high/critical)
            sentiment_score: Sentiment analysis score (0.0-1.0)

        Returns:
            Confirmation message with ticket and customer IDs
        """
        pool = ctx.deps

        async with pool.acquire() as conn:
            # Start a transaction
            async with conn.transaction():
                # UPSERT customer (insert or update on conflict)
                customer_id = await conn.fetchval("""
                    INSERT INTO customers (email, name)
                    VALUES ($1, $2)
                    ON CONFLICT (email)
                    DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                """, customer_email, customer_name)

                # Insert ticket with enum casting
                ticket_id = await conn.fetchval("""
                    INSERT INTO tickets (
                        customer_id,
                        raw_content,
                        summary,
                        category,
                        priority,
                        sentiment_score
                    )
                    VALUES ($1, $2, $3, $4::category_enum, $5::priority_enum, $6)
                    RETURNING id
                """, customer_id, raw_content, summary, category, priority, sentiment_score)

        return f"Successfully saved ticket #{ticket_id} for customer '{customer_name}' (ID: {customer_id})"
