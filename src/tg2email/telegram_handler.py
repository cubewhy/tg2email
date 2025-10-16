import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import re

from . import config
from . import database
from . import email_handler

# Set up logging
logger = logging.getLogger(__name__)

# --- Utility Functions ---

def is_admin(update: Update) -> bool:
    """Check if the message is from the configured admin user."""
    return update.effective_user.id == config.TELEGRAM_ADMIN_ID

def is_from_target_group(update: Update) -> bool:
    """Check if the message is from the configured target group."""
    return update.effective_chat.id == config.TELEGRAM_CHAT_ID

def is_valid_email(email: str) -> bool:
    """Simple regex check for email validity."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    if not is_admin(update):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    recipients = ", ".join(database.get_recipient_emails()) or "None"
    await update.message.reply_text(
        "Welcome to the Telegram-Email Bridge Bot!\n\n"
        "Available commands:\n"
        "/status - View current recipient emails.\n"
        "/set_emails <email1>,<email2>... - Set the recipient email addresses.\n"
        "/help - Show this message again.\n\n"
        f"Currently forwarding Telegram messages to: {recipients}"
    )

async def set_emails_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /set_emails command. Only admin can use it."""
    if not is_admin(update):
        await update.message.reply_text("You are not authorized to change settings.")
        return

    # context.args contains the list of strings after the command
    if not context.args:
        await update.message.reply_text(
            "Usage: /set_emails email1@example.com, email2@example.com\n"
            "You can also provide a single email or use spaces instead of commas."
        )
        return

    # Join args and then split by comma to handle both spaces and commas
    email_str = " ".join(context.args)
    potential_emails = [e.strip() for e in email_str.split(',') if e.strip()]

    valid_emails = [e for e in potential_emails if is_valid_email(e)]
    invalid_emails = [e for e in potential_emails if not is_valid_email(e)]

    if invalid_emails:
        await update.message.reply_text(f"The following emails are invalid and were ignored: {', '.join(invalid_emails)}")

    if not valid_emails:
        await update.message.reply_text("No valid emails provided. The recipient list remains unchanged.")
        return

    try:
        database.set_recipient_emails(valid_emails)
        await update.message.reply_text(f"✅ Recipient emails have been updated to: {', '.join(valid_emails)}")
    except Exception as e:
        logger.error(f"Error setting emails: {e}")
        await update.message.reply_text("An error occurred while updating the emails.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /status command."""
    if not is_admin(update):
        await update.message.reply_text("You are not authorized to view status.")
        return
        
    recipients = database.get_recipient_emails()
    if recipients:
        await update.message.reply_text(f"Currently forwarding messages to: {', '.join(recipients)}")
    else:
        await update.message.reply_text("No recipient emails are configured.")


# --- Message Handler ---

async def forward_telegram_to_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Forwards messages from the target Telegram group to the configured emails.
    """
    # Ensure this handler only works in the specified group
    if not is_from_target_group(update):
        return

    message = update.message
    sender_name = message.from_user.full_name
    message_text = message.text or "[This message has no text content, e.g., a sticker or photo]"

    # Format the email
    subject = f"[Telegram Bridge] New message from {sender_name}"
    body = f"Message from {sender_name} in the Telegram group:\n\n---\n\n{message_text}"

    # Send the email in a non-blocking way
    try:
        # Running a synchronous function in an async context
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, email_handler.send_email, subject, body)
    except Exception as e:
        logger.error(f"Error when trying to forward message to email: {e}")


def setup_handlers(application: Application):
    """Adds all command and message handlers to the application."""
    # Command handlers
    application.add_handler(CommandHandler("start", start_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("help", start_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("set_emails", set_emails_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("status", status_command, filters=filters.ChatType.PRIVATE))

    # Message handler for forwarding from the specific group
    # It filters for text messages in the target chat ID.
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Chat(chat_id=config.TELEGRAM_CHAT_ID),
        forward_telegram_to_email
    ))
    logger.info("Telegram handlers have been set up.")
