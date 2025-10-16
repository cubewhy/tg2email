import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigError(Exception):
    """Custom exception for missing configuration."""

    pass


def get_env_variable(var_name: str) -> str:
    """Get an environment variable or raise an exception."""
    value = os.getenv(var_name)
    if value is None:
        raise ConfigError(f"Error: Environment variable '{var_name}' not set.")
    return value


# --- Telegram Configuration ---
TELEGRAM_BOT_TOKEN = get_env_variable("TELEGRAM_BOT_TOKEN")
# Chat ID must be an integer
TELEGRAM_CHAT_ID = int(get_env_variable("TELEGRAM_CHAT_ID"))
# Admin ID must be an integer
TELEGRAM_ADMIN_ID = int(get_env_variable("TELEGRAM_ADMIN_ID"))


# --- IMAP (Receiving Email) Configuration ---
IMAP_SERVER = get_env_variable("IMAP_SERVER")
IMAP_USERNAME = get_env_variable("IMAP_USERNAME")
IMAP_PASSWORD = get_env_variable("IMAP_PASSWORD")

# --- SMTP (Sending Email) Configuration ---
SMTP_SERVER = get_env_variable("SMTP_SERVER")
# SMTP port must be an integer
SMTP_PORT = int(get_env_variable("SMTP_PORT"))
SMTP_USERNAME = get_env_variable("SMTP_USERNAME")
SMTP_PASSWORD = get_env_variable("SMTP_PASSWORD")
SENDER_EMAIL = get_env_variable("SENDER_EMAIL")

# --- Bridge Configuration ---
# Interval must be an integer
EMAIL_CHECK_INTERVAL_SECONDS = int(get_env_variable("EMAIL_CHECK_INTERVAL_SECONDS"))

# --- Database Configuration ---
DATABASE_FILE = "bridge_config.db"
