import sqlite3
import logging
from typing import List
from . import config

# Set up logging
logger = logging.getLogger(__name__)

def get_db_connection():
    """Gets a connection to the SQLite database."""
    conn = sqlite3.connect(config.DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database and creates the settings table if it doesn't exist.
    This function is idempotent.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()
            logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database error during initialization: {e}")
        raise

def get_recipient_emails() -> List[str]:
    """Retrieves the list of recipient email addresses from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'recipient_emails'")
            row = cursor.fetchone()
            if row and row['value']:
                # Split comma-separated string into a list of emails
                return [email.strip() for email in row['value'].split(',')]
            return []
    except sqlite3.Error as e:
        logger.error(f"Failed to get recipient emails from DB: {e}")
        return []

def set_recipient_emails(emails: List[str]):
    """
    Saves the list of recipient email addresses to the database.
    Emails are stored as a single comma-separated string.
    """
    # Join list of emails into a single comma-separated string
    emails_str = ','.join(emails)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Use INSERT OR REPLACE to either create the row or update it if it exists
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ('recipient_emails', emails_str)
            )
            conn.commit()
            logger.info(f"Recipient emails updated in database: {emails_str}")
    except sqlite3.Error as e:
        logger.error(f"Failed to set recipient emails in DB: {e}")
        raise
