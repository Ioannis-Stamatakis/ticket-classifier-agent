# Ticket Classifier Agent

An intelligent customer support ticket classification system powered by PydanticAI and Google Gemini AI. This system automatically analyzes support tickets to extract summaries, categorize issues, assign priority levels, and perform sentiment analysis.

## Features

- **AI-Powered Analysis**: Uses Google Gemini 2.5 Flash for intelligent ticket processing
- **Automatic Classification**: Categorizes tickets into billing, technical, feature requests, or general inquiries
- **Priority Assignment**: Automatically assigns priority levels (low, medium, high, critical)
- **Sentiment Analysis**: Evaluates customer sentiment with numerical scoring
- **Beautiful CLI Display**: Color-coded Rich tables showing recent tickets with visual priority indicators
- **Flexible Input Methods**: Command-line args, interactive mode, or default sample tickets
- **PostgreSQL Integration**: Robust data storage with custom ENUM types and optimized indexes
- **Async Architecture**: Built with asyncpg for high-performance database operations

## Architecture

### Technology Stack

- **PydanticAI**: AI agent framework for structured output
- **Google Gemini AI**: gemini-2.5-flash model for natural language processing
- **PostgreSQL**: Relational database with custom ENUM types
- **asyncpg**: Asynchronous PostgreSQL driver
- **SQLModel**: Type-safe ORM with Pydantic integration
- **Rich**: Beautiful terminal UI with color-coded tables
- **Python 3.8+**: Modern async/await patterns

### Data Flow

```
Customer Ticket → PydanticAI Agent → Google Gemini AI → Structured Output → PostgreSQL
```

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Google Gemini API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ioannis-Stamatakis/TicketClassifierAgent.git
   cd TicketClassifierAgent
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=ticket_db
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   ```

5. **Initialize database**

   The database schema will be automatically initialized on first run. The schema includes:
   - Custom ENUM types for categories and priorities
   - Customers and tickets tables
   - Optimized indexes for common queries

## Usage

### Process Tickets

The application supports three modes for ticket input:

**1. Default Sample Ticket**
```bash
python -m src.main
```
Processes a built-in sample ticket for testing.

**2. Command-Line Input**
```bash
python -m src.main "Subject: Need help with my account. Email: user@example.com Name: John Doe"
```
Provide the entire ticket content as a command-line argument.

**3. Interactive Mode**
```bash
python -m src.main --interactive
```
Enter ticket content interactively with multi-line support. Type `END` on a new line when finished.

### Rich CLI Display

After processing a ticket, the system displays a beautiful color-coded table showing the 5 most recent tickets:

**Features:**
- **Color-coded priorities**: Critical (bright red), High (red), Medium (yellow), Low (green)
- **Color-coded categories**: Billing (cyan), Technical (magenta), Feature Request (blue), General (white)
- **Sentiment indicators**: Percentage with emoji (positive 😊, neutral 😐, negative 😞)
- **Highlighted rows**: Newly processed tickets appear with a green background
- **Compact columns**: ID, Customer, Summary, Category, Priority, Sentiment

**Example Table Output:**
```
Recent Tickets (Last 5)
┏━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID ┃ Customer        ┃ Summary            ┃ Category  ┃ Priority ┃ Sentiment ┃
┡━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━┩
│  8 │ Sarah Johnson   │ Customer charged   │  Billing  │ CRITICAL │  10% 😞   │
│    │                 │ twice for sub...   │           │          │           │
├────┼─────────────────┼────────────────────┼───────────┼──────────┼───────────┤
│  7 │ Lisa Anderson   │ Thank you note     │  General  │   LOW    │  98% 😊   │
└────┴─────────────────┴────────────────────┴───────────┴──────────┴───────────┘
```

The table automatically updates after each ticket is processed, providing instant visual feedback on classification results.

### Add Test Tickets

Populate the database with diverse test tickets:

```bash
python scripts/add_test_tickets.py
```

This script adds 6 test tickets covering various scenarios:
- Billing issues with critical priority
- Technical problems (login, system outages)
- Feature requests
- General inquiries
- Positive customer feedback

### Example Output

```python
{
    "summary": "Customer unable to access account due to login failure",
    "category": "technical",
    "priority": "high",
    "sentiment_score": 0.2
}
```

Sentiment scores range from 0.0 (very negative) to 1.0 (very positive).

## Database Schema

### ENUM Types

```sql
priority_enum: low, medium, high, critical
category_enum: billing, technical, feature_request, general
```

### Tables

**customers**
- `id` (UUID, primary key)
- `email` (VARCHAR, unique)
- `name` (VARCHAR)
- `created_at` (TIMESTAMP)

**tickets**
- `id` (UUID, primary key)
- `customer_id` (UUID, foreign key)
- `raw_content` (TEXT)
- `summary` (TEXT)
- `category` (category_enum)
- `priority` (priority_enum)
- `sentiment_score` (FLOAT)
- `created_at` (TIMESTAMP)

### Indexes

- `idx_tickets_customer_id`: Fast customer ticket lookups
- `idx_tickets_category`: Filter by category
- `idx_tickets_priority`: Filter by priority
- `idx_customers_email`: Fast email lookups

## Project Structure

```
TicketClassifierAgent/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── scripts/
│   └── add_test_tickets.py    # Test data generator
├── src/
│   ├── main.py                # Application entry point
│   ├── config/
│   │   └── settings.py        # Configuration management
│   ├── models/
│   │   ├── database.py        # SQLModel database models
│   │   └── schemas.py         # Pydantic schemas
│   ├── database/
│   │   ├── connection.py      # Database connection pool
│   │   └── init_schema.sql    # Database schema
│   ├── agent/
│   │   ├── ticket_agent.py    # PydanticAI agent
│   │   └── tools.py           # Agent tools
│   ├── display/
│   │   ├── __init__.py        # Display module
│   │   └── table_display.py   # Rich CLI table rendering
│   └── utils/
│       └── enums.py           # Shared enumerations
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `DB_HOST` | PostgreSQL host | Yes |
| `DB_PORT` | PostgreSQL port | Yes |
| `DB_NAME` | Database name | Yes |
| `DB_USER` | Database user | Yes |
| `DB_PASSWORD` | Database password | Yes |

### Database Connection

The system automatically handles:
- URL encoding for special characters in credentials
- SSL configuration based on server support
- Connection pooling for optimal performance

## API Integration

### Google Gemini AI

The system uses Google Gemini 2.5 Flash model for:
- Natural language understanding
- Text summarization
- Classification and categorization
- Sentiment analysis

API authentication is handled via environment variables.

## Development

### Running Tests

```bash
pytest
```

### Code Style

The project follows Python best practices:
- Type hints for all functions
- Async/await patterns for I/O operations
- Pydantic models for data validation
- SQLModel for type-safe database operations

## Troubleshooting

### Common Issues

**Connection errors**
- Ensure PostgreSQL is running
- Verify credentials in `.env` file
- Check if special characters in password are URL-encoded

**SSL errors**
- The system automatically handles SSL configuration
- SSL is disabled by default for local development

**API errors**
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota and rate limits

## Future Enhancements

- [ ] REST API endpoint for ticket submission
- [ ] Batch processing for multiple tickets
- [ ] Real-time streaming analysis
- [ ] Enhanced agent tools for database operations
- [ ] Comprehensive test suite
- [ ] Database migrations with Alembic
- [ ] Multi-language support
- [ ] Customer feedback integration
- [ ] Analytics dashboard

## Dependencies

Core packages:
- `pydantic-ai>=0.0.13` - AI agent framework
- `google-generativeai>=0.8.0` - Google Gemini integration
- `asyncpg>=0.29.0` - Async PostgreSQL driver
- `sqlmodel>=0.0.22` - SQL ORM with Pydantic
- `python-dotenv>=1.0.0` - Environment management
- `pydantic>=2.0.0` - Data validation
- `rich>=13.7.0` - Terminal UI and table rendering

See `requirements.txt` for complete list.

## License

This project is available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

For questions or feedback, please open an issue on GitHub.

## Acknowledgments

- Built with [PydanticAI](https://ai.pydantic.dev/)
- Powered by [Google Gemini AI](https://ai.google.dev/)
- Database design inspired by PostgreSQL best practices
