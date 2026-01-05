"""Script to add test tickets to the database."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import Settings
from src.database.connection import create_pool, close_pool
from src.agent.ticket_agent import create_ticket_agent
from src.main import extract_customer_info


# Test tickets with different categories, priorities, and sentiments
TEST_TICKETS = [
    {
        "content": """
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
""",
        "description": "Billing - Duplicate charge (Critical, Negative)"
    },
    {
        "content": """
Subject: Can't login to my account

Hi there,

I've been trying to log into my account for the past hour but I keep getting an error message
saying "Invalid credentials" even though I'm 100% sure my password is correct. I've tried
resetting it twice already and the same issue happens.

This is really frustrating because I need to access my dashboard for an important presentation
tomorrow morning.

Account email: mike.chen@techcorp.com
Account name: Mike Chen

Thanks for your help.

Mike
""",
        "description": "Technical - Login issue (High, Negative)"
    },
    {
        "content": """
Subject: Feature Request - Dark Mode

Hello!

I absolutely love your product! I use it every day and it's been a game-changer for my workflow.

I was wondering if you could add a dark mode option? I often work late at night and it would
be much easier on my eyes. I noticed some of your competitors have this feature and it would
be amazing to have it in your app too.

Keep up the great work!

Best regards,
Account name: Emma Wilson
Account email: emma.wilson@design.io
""",
        "description": "Feature Request - Dark mode (Low, Positive)"
    },
    {
        "content": """
Subject: Question about pricing plans

Hi,

I'm currently on the Basic plan and I'm considering upgrading to Pro. Could you explain what
the main differences are? I see that Pro has "advanced analytics" but I'm not sure what that
includes exactly.

Also, if I upgrade mid-month, will I be charged the full amount or prorated?

Thanks!

Account name: James Rodriguez
Account email: j.rodriguez@startup.com
""",
        "description": "General - Pricing inquiry (Medium, Neutral)"
    },
    {
        "content": """
Subject: URGENT - System down, losing revenue!

THIS IS CRITICAL!!!

Our entire payment processing system has been down for 3 HOURS. We are losing thousands of
dollars every minute this continues. Our customers can't complete purchases and we're getting
bombarded with complaints.

This is absolutely UNACCEPTABLE for an enterprise plan customer. We need someone on this
IMMEDIATELY or we're switching providers and demanding a full refund.

Contact me NOW: 555-0199

Account name: David Park
Account email: david.park@enterprise.com
Director of Operations
""",
        "description": "Technical - System outage (Critical, Very Negative)"
    },
    {
        "content": """
Subject: Thank you for the excellent support!

Hi team,

I just wanted to send a quick note to say thank you for the amazing support I received
yesterday from Alex. He was patient, knowledgeable, and went above and beyond to help me
set up my integration.

Your product is fantastic and your support team makes it even better. Keep it up!

Cheers,
Account name: Lisa Anderson
Account email: lisa.anderson@creative.co
""",
        "description": "General - Thank you note (Low, Very Positive)"
    }
]


async def process_ticket(agent, pool, ticket_data):
    """Process a single ticket through the AI agent and save to database."""
    content = ticket_data["content"]
    description = ticket_data["description"]

    print(f"\n{'='*60}")
    print(f"Processing: {description}")
    print(f"{'='*60}")

    # Extract customer info
    customer_info = extract_customer_info(content)
    print(f"Customer: {customer_info['name']} ({customer_info['email']})")

    # Analyze with AI agent
    print("Analyzing with AI...")
    result = await agent.run(
        f"Analyze this customer support ticket:\n\n{content}",
        deps=pool
    )

    # Display results
    print(f"  Summary: {result.output.summary}")
    print(f"  Category: {result.output.category}")
    print(f"  Priority: {result.output.priority}")
    print(f"  Sentiment: {result.output.sentiment_score:.2f}")

    # Save to database
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
                content,
                result.output.summary,
                result.output.category,
                result.output.priority,
                result.output.sentiment_score
            )

    print(f"  ✓ Saved as Ticket #{ticket_id} for Customer #{customer_id}")
    return ticket_id


async def main():
    """Process all test tickets."""
    print("="*60)
    print("Adding Test Tickets to Database")
    print("="*60)

    pool = None
    try:
        # Load configuration
        print("\n[1/3] Loading configuration...")
        settings = Settings.from_env()
        print(f"  ✓ Connected to database: {settings.db_name}")

        # Initialize database connection
        print("\n[2/3] Creating database connection pool...")
        pool = await create_pool(settings.database_dsn)
        print("  ✓ Connection pool created")

        # Create AI agent
        print("\n[3/3] Creating AI agent...")
        agent = create_ticket_agent(settings.gemini_api_key)
        print("  ✓ Agent ready")

        # Process all test tickets
        print(f"\nProcessing {len(TEST_TICKETS)} test tickets...")
        ticket_ids = []
        for i, ticket_data in enumerate(TEST_TICKETS, 1):
            print(f"\n[Ticket {i}/{len(TEST_TICKETS)}]")
            ticket_id = await process_ticket(agent, pool, ticket_data)
            ticket_ids.append(ticket_id)

        # Summary
        print(f"\n{'='*60}")
        print("✓ All tickets processed successfully!")
        print(f"{'='*60}")
        print(f"Total tickets created: {len(ticket_ids)}")
        print(f"Ticket IDs: {', '.join(map(str, ticket_ids))}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        if pool is not None:
            print("\nClosing database connection pool...")
            await close_pool(pool)


if __name__ == "__main__":
    asyncio.run(main())
