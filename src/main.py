"""Main application entry point."""
import asyncio
import re
from src.config.settings import Settings
from src.database.connection import create_pool, init_database, close_pool
from src.agent.ticket_agent import create_ticket_agent


# Sample customer ticket for testing
SAMPLE_TICKET = """
Subject: Billing Error - Charged Twice This Month!

Hello,

I just checked my bank statement and noticed I was charged TWICE for my monthly subscription!
This is completely unacceptable. I've been a loyal customer for over 2 years and this has never
happened before.

I need this fixed IMMEDIATELY and I want a full refund for the duplicate charge. This better
not happen again or I'm canceling my subscription.

My account email is: sarah.johnson@email.com
Account name: Sarah Johnson

Please respond ASAP.

Frustrated,
Sarah Johnson
"""


def extract_customer_info(ticket_content: str) -> dict:
    """
    Simple extraction of customer info from ticket.

    In production, this could be more sophisticated or use the agent itself.
    """
    email = None
    name = None

    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, ticket_content)
    if matches:
        email = matches[0]

    # Extract name (look for "name:" pattern)
    for line in ticket_content.split('\n'):
        if 'name:' in line.lower():
            parts = line.split(':')
            if len(parts) > 1:
                name = parts[1].strip()
                break

    return {
        'email': email or 'unknown@example.com',
        'name': name or 'Unknown Customer'
    }


async def main():
    """Main application flow."""
    print("=" * 60)
    print("PydanticAI Ticket Classification System")
    print("=" * 60)

    pool = None
    try:
        # 1. Load configuration
        print("\n[1/5] Loading configuration...")
        settings = Settings.from_env()
        print(f"  ✓ Loaded settings for database: {settings.db_name}")

        # 2. Initialize database connection pool
        print("\n[2/5] Initializing database connection pool...")
        pool = await create_pool(settings.database_dsn)
        print("  ✓ Connection pool created")

        # 3. Initialize database schema
        print("\n[3/5] Initializing database schema...")
        await init_database(pool)
        print("  ✓ Schema initialized")

        # 4. Create ticket classification agent
        print("\n[4/5] Creating AI agent...")
        agent = create_ticket_agent(settings.gemini_api_key)
        print("  ✓ Agent created with Google Gemini (gemini-2.5-flash)")

        # 5. Process sample ticket
        print("\n[5/5] Processing sample ticket...")
        print("\n--- SAMPLE TICKET ---")
        print(SAMPLE_TICKET)
        print("--- END TICKET ---\n")

        # Extract customer info
        customer_info = extract_customer_info(SAMPLE_TICKET)
        print(f"  ✓ Extracted customer: {customer_info['name']} ({customer_info['email']})")

        # Run agent analysis
        print("\n  Analyzing ticket with AI agent...")
        result = await agent.run(
            f"Analyze this customer support ticket:\n\n{SAMPLE_TICKET}",
            deps=pool
        )

        # 6. Display results
        print("\n[6/6] Analysis Results:")
        print("=" * 60)
        print(f"  Summary: {result.output.summary}")
        print(f"  Category: {result.output.category}")
        print(f"  Priority: {result.output.priority}")
        print(f"  Sentiment Score: {result.output.sentiment_score:.2f}")
        print("=" * 60)

        # Save to database manually
        print("\n  Saving to database...")
        async with pool.acquire() as conn:
            async with conn.transaction():
                # UPSERT customer
                customer_id = await conn.fetchval("""
                    INSERT INTO customers (email, name)
                    VALUES ($1, $2)
                    ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                """, customer_info['email'], customer_info['name'])

                # Insert ticket
                ticket_id = await conn.fetchval("""
                    INSERT INTO tickets (
                        customer_id, raw_content, summary,
                        category, priority, sentiment_score
                    )
                    VALUES ($1, $2, $3, $4::category_enum, $5::priority_enum, $6)
                    RETURNING id
                """,
                    customer_id,
                    SAMPLE_TICKET,
                    result.output.summary,
                    result.output.category,
                    result.output.priority,
                    result.output.sentiment_score
                )

        print(f"  ✓ Saved as Ticket #{ticket_id} for Customer #{customer_id}")

        print("\n✓ Processing complete!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        # Cleanup
        if pool is not None:
            print("\nClosing database connection pool...")
            await close_pool(pool)
            print("✓ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
