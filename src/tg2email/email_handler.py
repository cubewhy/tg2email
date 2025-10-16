import smtplib
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from imap_tools.mailbox import MailBox
from imap_tools.message import MailMessage
from telegram import Bot

from . import config
from . import database

# Set up logging
logger = logging.getLogger(__name__)

def send_email(subject: str, body: str):
    """
    Sends an email to the recipients stored in the database.
    """
    recipients = database.get_recipient_emails()
    if not recipients:
        logger.warning("Attempted to send email, but no recipients are configured.")
        return

    msg = MIMEMultipart()
    msg['From'] = config.SENDER_EMAIL
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.sendmail(config.SENDER_EMAIL, recipients, msg.as_string())
            logger.info(f"Email sent to {recipients} with subject: {subject}")
    except smtplib.SMTPException as e:
        logger.error(f"Failed to send email: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email: {e}")


async def email_checker_loop(bot: Bot):
    """
    Periodically checks for new emails and forwards them to Telegram.
    This function runs in an infinite loop.
    """
    logger.info("Starting email checker loop...")
    while True:
        try:
            mailbox_client = MailBox(
                host=config.IMAP_SERVER,
                port=config.IMAP_PORT
            )
            
            # Use a context manager to handle login/logout
            with mailbox_client.login(config.IMAP_USERNAME, config.IMAP_PASSWORD, 'INBOX') as mailbox:
                # Fetch unseen emails and mark them as seen
                unseen_messages = list(mailbox.fetch(criteria="UNSEEN", mark_seen=True))
                if unseen_messages:
                    logger.info(f"Found {len(unseen_messages)} new email(s).")
                    for msg in unseen_messages:
                        await _forward_email_to_telegram(msg, bot)
                else:
                    logger.debug("No new emails found.")

        except Exception as e:
            logger.error(f"Error in email checker loop: {e}")

        # Wait for the configured interval before checking again
        await asyncio.sleep(config.EMAIL_CHECK_INTERVAL_SECONDS)


async def _forward_email_to_telegram(msg: MailMessage, bot: Bot):
    """
    Formats an email message and sends it to the configured Telegram chat.
    """
    # Format the message for Telegram
    # Using msg.text for plain text content is usually safer for Telegram
    email_body = msg.text or "This email contains no plain text content."
    
    # Truncate long emails to avoid hitting Telegram's message limit
    if len(email_body) > 3800:
        email_body = email_body[:3800] + "\n\n[Message truncated]"

    formatted_message = (
        f"📧 *New Email Received* 📧\n\n"
        f"*From:* `{msg.from_}`\n"
        f"*Subject:* `{msg.subject}`\n\n"
        f"------------------\n"
        f"{email_body}"
    )

    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=formatted_message,
            parse_mode='Markdown'
        )
        logger.info(f"Forwarded email from {msg.from_} to Telegram.")
    except Exception as e:
        logger.error(f"Failed to forward email to Telegram: {e}")
