"""Rich table display for ticket visualization."""
from typing import Optional
import asyncpg
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


def get_priority_color(priority: str) -> str:
    """
    Return Rich color string for priority level.

    Args:
        priority: Priority level (low, medium, high, critical)

    Returns:
        Rich color name
    """
    color_map = {
        "critical": "bright_red",
        "high": "red",
        "medium": "yellow",
        "low": "green"
    }
    return color_map.get(priority.lower(), "white")


def get_category_color(category: str) -> str:
    """
    Return Rich color string for category.

    Args:
        category: Category type (billing, technical, feature_request, general)

    Returns:
        Rich color name
    """
    color_map = {
        "billing": "cyan",
        "technical": "magenta",
        "feature_request": "blue",
        "general": "white"
    }
    return color_map.get(category.lower(), "white")


def get_sentiment_color(score: float) -> str:
    """
    Return Rich color string for sentiment score.

    Args:
        score: Sentiment score (0.0-1.0)

    Returns:
        Rich color name
    """
    if score < 0.4:
        return "red"
    elif score < 0.6:
        return "yellow"
    else:
        return "green"


def get_sentiment_emoji(score: float) -> str:
    """
    Return emoji indicator for sentiment score.

    Args:
        score: Sentiment score (0.0-1.0)

    Returns:
        Emoji string
    """
    if score < 0.4:
        return "😞"
    elif score < 0.6:
        return "😐"
    else:
        return "😊"


def format_sentiment(score: float) -> str:
    """
    Format sentiment as percentage with emoji.

    Args:
        score: Sentiment score (0.0-1.0)

    Returns:
        Formatted string like "85% 😊"
    """
    percentage = int(score * 100)
    emoji = get_sentiment_emoji(score)
    return f"{percentage}% {emoji}"


def truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to max_length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with "..." if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


async def fetch_recent_tickets(pool: asyncpg.Pool, limit: int = 5) -> list[dict]:
    """
    Fetch most recent tickets with customer information.

    Args:
        pool: Database connection pool
        limit: Number of tickets to fetch (default 5)

    Returns:
        List of ticket dictionaries with customer data
    """
    query = """
        SELECT
            t.id,
            t.summary,
            t.category,
            t.priority,
            t.sentiment_score,
            t.created_at,
            c.name as customer_name,
            c.email as customer_email
        FROM tickets t
        JOIN customers c ON t.customer_id = c.id
        ORDER BY t.created_at DESC
        LIMIT $1
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, limit)

    # Convert asyncpg Records to dictionaries
    return [dict(row) for row in rows]


async def fetch_filtered_tickets(
    pool: asyncpg.Pool,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 20
) -> list[dict]:
    """
    Fetch tickets filtered by category and/or priority.

    Args:
        pool: Database connection pool
        category: Optional category filter value
        priority: Optional priority filter value
        limit: Maximum number of tickets to fetch

    Returns:
        List of ticket dictionaries with customer data
    """
    base_query = """
        SELECT
            t.id,
            t.summary,
            t.category,
            t.priority,
            t.sentiment_score,
            t.created_at,
            c.name as customer_name,
            c.email as customer_email
        FROM tickets t
        JOIN customers c ON t.customer_id = c.id
    """

    conditions = []
    params = []
    param_idx = 1

    if category:
        conditions.append(f"t.category = ${param_idx}::category_enum")
        params.append(category)
        param_idx += 1

    if priority:
        conditions.append(f"t.priority = ${param_idx}::priority_enum")
        params.append(priority)
        param_idx += 1

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += f" ORDER BY t.created_at DESC LIMIT ${param_idx}"
    params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(base_query, *params)

    return [dict(row) for row in rows]


async def display_filtered_tickets(
    pool: asyncpg.Pool,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 20
) -> None:
    """
    Display filtered tickets in a Rich table.

    Args:
        pool: Database connection pool
        category: Optional category filter value
        priority: Optional priority filter value
        limit: Maximum number of tickets to display
    """
    console = Console(force_terminal=True)

    filter_parts = []
    if category:
        filter_parts.append(f"category={category}")
    if priority:
        filter_parts.append(f"priority={priority}")
    filter_desc = ", ".join(filter_parts)

    try:
        tickets = await fetch_filtered_tickets(pool, category, priority, limit)

        if not tickets:
            panel = Panel(
                f"[yellow]No tickets found matching filter: {filter_desc}[/yellow]",
                title="Filtered Tickets",
                border_style="yellow"
            )
            console.print(panel)
            return

        table = Table(
            title=f"[bold cyan]Filtered Tickets ({filter_desc}) - {len(tickets)} result(s)[/bold cyan]",
            title_justify="left",
            border_style="bright_black",
            show_header=True,
            header_style="bold cyan",
            show_lines=True,
            padding=(0, 1)
        )

        table.add_column("ID", justify="right", style="dim", no_wrap=True)
        table.add_column("Customer", justify="left", no_wrap=True)
        table.add_column("Summary", justify="left", max_width=60, overflow="fold")
        table.add_column("Category", justify="center", no_wrap=True)
        table.add_column("Priority", justify="center", no_wrap=True)
        table.add_column("Sentiment", justify="center", no_wrap=True)

        for ticket in tickets:
            ticket_id = str(ticket['id'])
            customer = truncate_text(ticket['customer_name'], 15)
            summary = ticket['summary']

            category_val = ticket['category']
            category_color = get_category_color(category_val)
            category_text = Text(category_val.replace('_', ' ').title(), style=category_color)

            priority_val = ticket['priority']
            priority_color = get_priority_color(priority_val)
            priority_style = f"{priority_color} bold" if priority_val.lower() == "critical" else priority_color
            priority_text = Text(priority_val.upper(), style=priority_style)

            sentiment_score = ticket['sentiment_score']
            sentiment_str = format_sentiment(sentiment_score)
            sentiment_color = get_sentiment_color(sentiment_score)
            sentiment_text = Text(sentiment_str, style=sentiment_color)

            table.add_row(
                ticket_id,
                customer,
                summary,
                category_text,
                priority_text,
                sentiment_text,
            )

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error displaying filtered tickets: {e}[/red]")
        raise


async def display_stats(pool: asyncpg.Pool) -> None:
    """
    Display an analytics dashboard of all tickets in the database.

    Args:
        pool: Database connection pool
    """
    console = Console(force_terminal=True)

    try:
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM tickets")

            if not total:
                console.print(Panel(
                    "[yellow]No tickets found. Process your first ticket![/yellow]",
                    title="Ticket Stats",
                    border_style="yellow"
                ))
                return

            by_category = await conn.fetch("""
                SELECT category::text, COUNT(*) AS count, AVG(sentiment_score) AS avg_sentiment
                FROM tickets
                GROUP BY category
                ORDER BY count DESC
            """)

            by_priority = await conn.fetch("""
                SELECT priority::text, COUNT(*) AS count
                FROM tickets
                GROUP BY priority
                ORDER BY count DESC
            """)

            overall_sentiment = await conn.fetchval("SELECT AVG(sentiment_score) FROM tickets")

            last_7 = await conn.fetchval(
                "SELECT COUNT(*) FROM tickets WHERE created_at >= NOW() - INTERVAL '7 days'"
            )
            last_30 = await conn.fetchval(
                "SELECT COUNT(*) FROM tickets WHERE created_at >= NOW() - INTERVAL '30 days'"
            )

        # --- Overview panel ---
        sentiment_color = get_sentiment_color(overall_sentiment)
        overview_lines = (
            f"[bold]Total Tickets:[/bold]  {total}\n"
            f"[bold]Avg Sentiment:[/bold]  [{sentiment_color}]{format_sentiment(overall_sentiment)}[/{sentiment_color}]\n"
            f"[bold]Last 7 days:[/bold]   {last_7}\n"
            f"[bold]Last 30 days:[/bold]  {last_30}"
        )
        console.print()
        console.print(Panel(overview_lines, title="[bold cyan]Ticket Stats Overview[/bold cyan]", border_style="cyan"))

        # --- By category table ---
        cat_table = Table(
            title="[bold cyan]Breakdown by Category[/bold cyan]",
            title_justify="left",
            border_style="bright_black",
            header_style="bold cyan",
            show_lines=True,
            padding=(0, 1)
        )
        cat_table.add_column("Category", justify="left")
        cat_table.add_column("Tickets", justify="right")
        cat_table.add_column("Avg Sentiment", justify="center")

        for row in by_category:
            cat = row["category"]
            color = get_category_color(cat)
            avg = row["avg_sentiment"]
            cat_table.add_row(
                Text(cat.replace("_", " ").title(), style=color),
                str(row["count"]),
                Text(format_sentiment(avg), style=get_sentiment_color(avg)),
            )
        console.print(cat_table)

        # --- By priority table ---
        pri_table = Table(
            title="[bold cyan]Breakdown by Priority[/bold cyan]",
            title_justify="left",
            border_style="bright_black",
            header_style="bold cyan",
            show_lines=True,
            padding=(0, 1)
        )
        pri_table.add_column("Priority", justify="left")
        pri_table.add_column("Tickets", justify="right")

        for row in by_priority:
            pri = row["priority"]
            color = get_priority_color(pri)
            style = f"{color} bold" if pri == "critical" else color
            pri_table.add_row(
                Text(pri.upper(), style=style),
                str(row["count"]),
            )
        console.print(pri_table)
        console.print()

    except Exception as e:
        console.print(f"[red]Error displaying stats: {e}[/red]")
        raise


async def display_recent_tickets(
    pool: asyncpg.Pool,
    limit: int = 5,
    highlight_id: Optional[int] = None
) -> None:
    """
    Display recent tickets in a Rich table.

    Args:
        pool: Database connection pool
        limit: Number of recent tickets to display
        highlight_id: Optional ticket ID to highlight (newly processed)
    """
    console = Console(force_terminal=True)

    try:
        # Fetch tickets
        tickets = await fetch_recent_tickets(pool, limit)

        # Handle empty database
        if not tickets:
            panel = Panel(
                "[yellow]No tickets found. Process your first ticket![/yellow]",
                title="Recent Tickets",
                border_style="yellow"
            )
            console.print(panel)
            return

        # Create table
        table = Table(
            title=f"[bold cyan]Recent Tickets (Last {len(tickets)})[/bold cyan]",
            title_justify="left",
            border_style="bright_black",
            show_header=True,
            header_style="bold cyan",
            show_lines=True,
            padding=(0, 1)
        )

        # Add columns with flexible widths (no fixed width for better terminal compatibility)
        table.add_column("ID", justify="right", style="dim", no_wrap=True)
        table.add_column("Customer", justify="left", no_wrap=True)
        table.add_column("Summary", justify="left", max_width=60, overflow="fold")
        table.add_column("Category", justify="center", no_wrap=True)
        table.add_column("Priority", justify="center", no_wrap=True)
        table.add_column("Sentiment", justify="center", no_wrap=True)

        # Add rows
        for ticket in tickets:
            # Determine if this row should be highlighted
            is_new = highlight_id and ticket['id'] == highlight_id
            row_style = "on dark_green" if is_new else None

            # Format data
            ticket_id = str(ticket['id'])
            customer = truncate_text(ticket['customer_name'], 15)
            summary = ticket['summary']  # No truncation - let Rich handle wrapping

            # Category with color
            category = ticket['category']
            category_color = get_category_color(category)
            category_text = Text(category.replace('_', ' ').title(), style=category_color)

            # Priority with color and bold for critical
            priority = ticket['priority']
            priority_color = get_priority_color(priority)
            priority_style = f"{priority_color} bold" if priority.lower() == "critical" else priority_color
            priority_text = Text(priority.upper(), style=priority_style)

            # Sentiment with color and emoji
            sentiment_score = ticket['sentiment_score']
            sentiment_str = format_sentiment(sentiment_score)
            sentiment_color = get_sentiment_color(sentiment_score)
            sentiment_text = Text(sentiment_str, style=sentiment_color)

            # Add row
            table.add_row(
                ticket_id,
                customer,
                summary,
                category_text,
                priority_text,
                sentiment_text,
                style=row_style
            )

        # Print table
        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        # Fallback to error message
        console.print(f"[red]Error displaying tickets: {e}[/red]")
        raise
