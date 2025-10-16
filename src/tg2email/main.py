# src/main.py

import asyncio
import logging
import sys

from telegram.ext import Application
from . import config
from . import database
from . import telegram_handler
from . import email_handler

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def main():
    """
    Main asynchronous function to initialize and run the bridge.
    """
    logger.info("Starting Telegram-Email Bridge...")

    try:
        database.init_db()
    except Exception as e:
        logger.critical(f"Fatal: Could not initialize database. Aborting. Error: {e}")
        return

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    telegram_handler.setup_handlers(application)

    try:
        logger.info("Running application components...")
        await asyncio.gather(
            application.run_polling(),
            email_handler.email_checker_loop(application.bot)
        )
    except Exception as e:
        logger.critical(f"A critical error occurred in the main event loop: {e}")
    finally:
        logger.info("Application shutting down.")


def run():
    """
    Synchronous entry point for the console script.
    Handles setup and gracefully runs the main async loop.
    """
    try:
        asyncio.run(main())
    except config.ConfigError as e:
        # Using print here because logger might not be configured if .env fails early
        print(f"CRITICAL: Configuration Error: {e}. Please check your .env file.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Shutting down.")
    except Exception as e:
        print(f"CRITICAL: An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    # This block allows the script to still be run with `python -m src.main`
    run()
