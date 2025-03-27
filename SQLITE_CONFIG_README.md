# SQLite Configuration for Smart Financial Analyzer

The Smart Financial Analyzer application has been configured to use SQLite as the database backend. This document provides information about this configuration and how to use it.

## Current Database Configuration

The application uses SQLite with the following configuration in `app.py`:

```python
# Use SQLite for database (simpler configuration)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///financial_analyzer.db")
```

This creates a file called `financial_analyzer.db` in your project directory, which contains all your application data.

## Advantages of SQLite

- **Simplicity**: No need for a separate database server
- **Zero configuration**: Works out of the box
- **Portability**: Your entire database is in a single file
- **Perfect for development**: Easy to work with during development

## Database Schema

The application uses SQLAlchemy ORM with the following models:

- **User**: User accounts and preferences
- **StockData**: Stock information and historical data
- **NewsItem**: Financial news articles
- **BookInsight**: Financial book summaries and insights
- **UserQuery**: User questions and LLM responses

## Using External APIs

When running the application, you'll need API keys for full functionality:

1. **Groq API Key**: For LLM capabilities (financial analysis, recommendations)
2. **Tavily API Key**: For news gathering (optional)

If these API keys are not provided, the services will run in simplified mode with limited functionality.

## Switching to PostgreSQL or MongoDB

If you need to switch to a more robust database for production:

- For PostgreSQL: Update the `DATABASE_URL` environment variable with a PostgreSQL connection string
- For MongoDB: See the migration guide in `MONGODB_MIGRATION_GUIDE.md`

## Limitations

While SQLite is great for development, it has limitations for production environments:

- Limited concurrency (doesn't handle multiple write operations well)
- No built-in user authentication/authorization mechanisms
- No network access (local file only)

## Database Management

To view or modify the database directly, you can use tools like:

- [SQLite Browser](https://sqlitebrowser.org/) - GUI tool for SQLite
- SQLite command line tool 

## Backup and Restore

To backup your database, simply copy the `financial_analyzer.db` file. To restore, replace it with your backup copy.