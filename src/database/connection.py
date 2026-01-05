"""Database connection pool management."""
import asyncpg
from pathlib import Path


async def create_pool(dsn: str, min_size: int = 2, max_size: int = 10) -> asyncpg.Pool:
    """
    Create an asyncpg connection pool.

    Args:
        dsn: PostgreSQL connection string
        min_size: Minimum pool size
        max_size: Maximum pool size

    Returns:
        Configured connection pool
    """
    # Disable SSL since the server doesn't support it
    return await asyncpg.create_pool(
        dsn,
        min_size=min_size,
        max_size=max_size,
        command_timeout=60,
        ssl=False
    )


async def init_database(pool: asyncpg.Pool) -> None:
    """
    Initialize database schema using SQL file.

    Args:
        pool: Database connection pool
    """
    # Read SQL initialization script
    sql_file = Path(__file__).parent / "init_schema.sql"
    schema_sql = sql_file.read_text()

    # Execute schema initialization
    async with pool.acquire() as conn:
        await conn.execute(schema_sql)
        print("Database schema initialized successfully")


async def close_pool(pool: asyncpg.Pool) -> None:
    """
    Close database connection pool.

    Args:
        pool: Database connection pool
    """
    await pool.close()
    print("Database connection pool closed")
