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

    # Create the Application instance
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Set up the command and message handlers
    telegram_handler.setup_handlers(application)

    # The modern, correct way to run the bot alongside other tasks.
    # `async with application:` handles startup (initialize()) and shutdown gracefully.
    async with application:
        logger.info("Starting bot polling and email checker...")
        try:
            # We start the polling in the background. `start_polling` is non-blocking.
            await application.updater.start_polling()

            # Now we can run our other coroutines concurrently.
            await asyncio.gather(
                email_handler.email_checker_loop(application.bot)
                # Note: We no longer put the bot itself in gather.
                # The `async with` block keeps it alive.
                # If you had more tasks, you'd add them here.
            )

        except Exception as e:
            logger.critical(f"A critical error occurred in the main event loop: {e}")
        finally:
            logger.info("Stopping bot polling...")
            # The context manager will handle the shutdown, but we should stop the updater.
            if application.updater.is_running:
                await application.updater.stop()


def run():
    """
    Synchronous entry point for the console script.
    """
    try:
        asyncio.run(main())
    except config.ConfigError as e:
        print(f"CRITICAL: Configuration Error: {e}. Please check your .env file.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Shutting down.")
    except Exception as e:
        print(f"CRITICAL: An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    run()
