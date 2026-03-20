"""Main application entry point."""
import asyncio
import re
import sys
from src.config.settings import Settings
from src.database.connection import create_pool, init_database, close_pool
from src.agent.ticket_agent import create_ticket_agent
from src.display.table_display import display_recent_tickets, display_filtered_tickets, display_stats
from src.export.csv_export import export_tickets_to_csv
from src.utils.enums import Category, Priority


# Sample customer tickets for testing
SAMPLE_TICKETS = [
    """
Subject: Billing Error - Charged Twice This Month!

Hello,

I just checked my bank statement and noticed I was charged TWICE for my monthly subscription!
This is completely unacceptable. I've been a loyal customer for over 2 years and this has never
happened before.

I need this fixed IMMEDIATELY and I want a full refund for the duplicate charge. This better
not happen again or I'm canceling my subscription.

Email: sarah.johnson@email.com
Name: Sarah Johnson

Please respond ASAP.

Frustrated,
Sarah Johnson
""",
    """
Subject: Cannot Login to My Account

Hi Support Team,

I've been trying to log into my account for the past hour but keep getting an "Invalid credentials"
error. I'm 100% sure I'm using the correct password. I even tried the forgot password link but
never received the reset email.

This is preventing me from accessing important documents I need for work today. Can someone please
help me regain access as soon as possible?

Email: michael.chen@techcorp.com
Name: Michael Chen

Thanks,
Michael
""",
    """
Subject: Feature Request - Dark Mode

Hello!

I absolutely love your application and use it every day. However, I work late nights and the bright
white interface can be quite straining on my eyes. Would it be possible to add a dark mode option?

I know many users have been asking for this feature on your forums. It would be a great quality of
life improvement!

Email: emma.davis@design.io
Name: Emma Davis

Keep up the great work!
Emma
""",
    """
Subject: Question About Pricing Plans

Hi there,

I'm currently on the Basic plan but considering upgrading to Pro. Could you help me understand the
differences between the two plans? Specifically, I'm interested in knowing about storage limits and
the number of team members I can add.

Also, if I upgrade mid-month, will I be charged the full amount or prorated?

Email: alex.rivera@startup.com
Name: Alex Rivera

Thank you!
Alex
""",
    """
Subject: Thank You!

Dear Support Team,

I just wanted to take a moment to thank you for the excellent customer service I received yesterday.
Jessica helped me resolve my technical issue within minutes and was incredibly patient and professional.

It's rare to find such dedicated support these days. You have a great team!

Email: olivia.martinez@email.com
Name: Olivia Martinez

Best regards,
Olivia
"""
]

import random

# Select a random sample ticket for default mode
SAMPLE_TICKET = random.choice(SAMPLE_TICKETS)


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

    # Extract name (look for "name:" pattern or "Name:" at start of word)
    for line in ticket_content.split('\n'):
        if 'name:' in line.lower():
            # Split only on the first colon after "name"
            idx = line.lower().find('name:')
            if idx != -1:
                name = line[idx + 5:].strip()
                break

    return {
        'email': email or 'unknown@example.com',
        'name': name or 'Unknown Customer'
    }


def get_export_args() -> tuple[bool, str]:
    """
    Check if --export / -e flag is present in command line args.

    Returns:
        Tuple of (should_export, output_filename)
    """
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ('--export', '-e'):
            # Check if next arg is a filename (not another flag)
            if i + 1 <= len(sys.argv) - 1 and not sys.argv[i + 1].startswith('-'):
                return True, sys.argv[i + 1]
            return True, "tickets_export.csv"
    return False, ""


def get_filter_args() -> tuple[bool, str | None, str | None]:
    """
    Check if --filter / -f flag is present and parse the filter expression.

    Returns:
        Tuple of (should_filter, category_value, priority_value)
    """
    valid_categories = {e.value for e in Category}
    valid_priorities = {e.value for e in Priority}

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ('--filter', '-f'):
            if i + 1 > len(sys.argv) - 1:
                print("Error: --filter requires a value (e.g. --filter category=billing)")
                sys.exit(1)

            filter_expr = sys.argv[i + 1]
            if '=' not in filter_expr:
                print(f"Error: Invalid filter format '{filter_expr}'. Use key=value (e.g. category=billing)")
                sys.exit(1)

            key, value = filter_expr.split('=', 1)
            key = key.strip().lower()
            value = value.strip().lower()

            if key == 'category':
                if value not in valid_categories:
                    print(f"Error: Invalid category '{value}'. Valid: {', '.join(sorted(valid_categories))}")
                    sys.exit(1)
                return True, value, None
            elif key == 'priority':
                if value not in valid_priorities:
                    print(f"Error: Invalid priority '{value}'. Valid: {', '.join(sorted(valid_priorities))}")
                    sys.exit(1)
                return True, None, value
            else:
                print(f"Error: Unknown filter key '{key}'. Valid keys: category, priority")
                sys.exit(1)

    return False, None, None


def get_ticket_input() -> str:
    """
    Get ticket content from command line args or interactive input.

    Returns:
        Ticket content string or list of tickets
    """
    # Check if ticket provided as command line argument
    if len(sys.argv) > 1:
        if sys.argv[1] == '--interactive' or sys.argv[1] == '-i':
            return get_interactive_ticket()
        elif sys.argv[1] == '--all' or sys.argv[1] == '-a':
            # Return all sample tickets for batch processing
            return 'ALL_SAMPLES'
        elif sys.argv[1] in ('--export', '-e'):
            # Export mode handled separately in main()
            return 'EXPORT'
        elif sys.argv[1] in ('--filter', '-f'):
            # Filter mode handled separately in main()
            return 'FILTER'
        elif sys.argv[1] in ('--stats', '-s'):
            return 'STATS'
        else:
            # Treat all args as the ticket content
            return ' '.join(sys.argv[1:])

    # Use random sample ticket by default
    return SAMPLE_TICKET


def get_interactive_ticket() -> str:
    """
    Get ticket content via interactive multi-line input.

    Returns:
        Ticket content string
    """
    print("\nEnter your ticket content (type 'END' on a new line when done):")
    print("-" * 60)

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
        except EOFError:
            break

    return '\n'.join(lines)


async def process_single_ticket(ticket_content: str, agent, pool):
    """Process a single ticket and return the ticket ID."""
    print("\n--- TICKET CONTENT ---")
    print(ticket_content)
    print("--- END TICKET ---\n")

    # Extract customer info
    customer_info = extract_customer_info(ticket_content)
    print(f"  ✓ Extracted customer: {customer_info['name']} ({customer_info['email']})")

    # Run agent analysis
    print("  Analyzing ticket with AI agent...")
    result = await agent.run(
        f"Analyze this customer support ticket:\n\n{ticket_content}",
        deps=pool
    )

    # Save to database
    print("  Saving to database...")
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
                ticket_content,
                result.output.summary,
                result.output.category,
                result.output.priority,
                result.output.sentiment_score
            )

    print(f"  ✓ Saved as Ticket #{ticket_id} for Customer #{customer_id}\n")
    return ticket_id


async def main():
    """Main application flow."""
    print("=" * 60)
    print("PydanticAI Ticket Classification System")
    print("=" * 60)
    print("\nUsage:")
    print("  python -m src.main                    # Use random sample ticket")
    print("  python -m src.main --all              # Process all 5 sample tickets")
    print("  python -m src.main --interactive      # Enter ticket interactively")
    print("  python -m src.main --export           # Export tickets to CSV")
    print("  python -m src.main --export out.csv   # Export to custom filename")
    print("  python -m src.main --filter category=billing  # Filter by category")
    print("  python -m src.main --filter priority=high     # Filter by priority")
    print("  python -m src.main --stats                   # Show analytics dashboard")
    print("  python -m src.main \"Your ticket...\"   # Provide ticket as argument")
    print("=" * 60)

    pool = None
    try:
        # Get ticket content from input
        ticket_input = get_ticket_input()

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

        # Handle export mode (no AI agent needed)
        should_export, export_filename = get_export_args()
        if should_export:
            from rich.console import Console
            console = Console(force_terminal=True)
            console.print(f"\n[bold cyan]Exporting tickets to:[/bold cyan] {export_filename}")
            count = await export_tickets_to_csv(pool, limit=50, output_path=export_filename)
            if count > 0:
                console.print(f"[green]  ✓ Exported {count} ticket(s) to {export_filename}[/green]")
            else:
                console.print("[yellow]  No tickets found to export.[/yellow]")
            return

        # Handle filter mode (no AI agent needed)
        should_filter, filter_category, filter_priority = get_filter_args()
        if should_filter:
            await display_filtered_tickets(
                pool=pool,
                category=filter_category,
                priority=filter_priority,
            )
            return

        # Handle stats mode (no AI agent needed)
        if ticket_input == 'STATS':
            await display_stats(pool)
            return

        # 4. Create ticket classification agent
        print("\n[4/5] Creating AI agent...")
        agent = create_ticket_agent(settings.gemini_api_key)
        print("  ✓ Agent created with Google Gemini (gemini-2.5-flash)")

        # 5. Process ticket(s)
        if ticket_input == 'ALL_SAMPLES':
            # Process all 5 sample tickets
            print(f"\n[5/5] Processing all {len(SAMPLE_TICKETS)} sample tickets...")
            last_ticket_id = None
            for i, ticket_content in enumerate(SAMPLE_TICKETS, 1):
                print(f"\n{'='*60}")
                print(f"Processing Ticket {i}/{len(SAMPLE_TICKETS)}")
                print(f"{'='*60}")
                last_ticket_id = await process_single_ticket(ticket_content, agent, pool)

            # Display table with the last processed ticket highlighted
            print(f"\n[6/6] Displaying Recent Tickets:")
            await display_recent_tickets(
                pool=pool,
                limit=5,
                highlight_id=last_ticket_id
            )
        else:
            # Process single ticket
            print("\n[5/5] Processing ticket...")
            ticket_id = await process_single_ticket(ticket_input, agent, pool)

            # Display results in Rich table
            print(f"[6/6] Displaying Recent Tickets:")
            await display_recent_tickets(
                pool=pool,
                limit=5,
                highlight_id=ticket_id
            )

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
