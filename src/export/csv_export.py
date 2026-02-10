"""CSV export functionality for tickets."""
import csv
from pathlib import Path
import asyncpg
from src.display.table_display import fetch_recent_tickets


async def export_tickets_to_csv(
    pool: asyncpg.Pool,
    limit: int = 50,
    output_path: str = "tickets_export.csv"
) -> int:
    """
    Export recent tickets to a CSV file.

    Args:
        pool: Database connection pool
        limit: Number of recent tickets to export
        output_path: Output CSV file path

    Returns:
        Number of exported rows
    """
    tickets = await fetch_recent_tickets(pool, limit)

    if not tickets:
        return 0

    fieldnames = [
        "ID", "Customer Name", "Customer Email", "Summary",
        "Category", "Priority", "Sentiment Score", "Created At"
    ]

    path = Path(output_path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for ticket in tickets:
            writer.writerow({
                "ID": ticket["id"],
                "Customer Name": ticket["customer_name"],
                "Customer Email": ticket["customer_email"],
                "Summary": ticket["summary"],
                "Category": ticket["category"],
                "Priority": ticket["priority"],
                "Sentiment Score": ticket["sentiment_score"],
                "Created At": ticket["created_at"].isoformat()
                    if hasattr(ticket["created_at"], "isoformat")
                    else str(ticket["created_at"]),
            })

    return len(tickets)
