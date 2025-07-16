import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
TASKS, WALLET = range(2)

# Milmotif specific links
TELEGRAM_GROUP = "https://t.me/milmotifgroup"
TWITTER_PROFILE = "https://x.com/milmotif"
OPENSEA_GALLERY = "https://opensea.io/milmotifart/galleries"
OPENSEA_WEBSITE = "https://opensea.io/milmotifart"

# Store completed users (in-memory, persists until bot restarts)
completed_users = set()

def create_task_keyboard():
    """Create inline keyboard for tasks with formatted links"""
    keyboard = [
        [InlineKeyboardButton("🔗 Join Milmotif Community", url=TELEGRAM_GROUP)],
        [InlineKeyboardButton("🐦 Follow us on Twitter", url=TWITTER_PROFILE)],
        [InlineKeyboardButton("🌐 View NFTs on OpenSea", url=OPENSEA_GALLERY)],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send instructions and set initial state"""
    user = update.effective_user
    
    # Check if user already completed
    if user.id in completed_users:
        await update.message.reply_text(
            "🎉 You have completed the Milmotif NFT Giveaway. Thank you!",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    # Create formatted welcome message
    welcome_msg = (
        f"🌟 Welcome {user.first_name} to the Official Milmotif NFT Giveaway! 🌟\n\n"
        "📋 **To participate, please complete these tasks:**\n"
        "1. Join our Telegram Community\n"
        "2. Follow us on Twitter\n"
        "3. Visit our OpenSea Gallery\n\n"
        "✅ **Send 'done' when you have completed all the tasks.**"
    )
    
    # Send message with inline buttons
    await update.message.reply_text(
        welcome_msg,
        parse_mode="Markdown",
        reply_markup=create_task_keyboard()
    )
    return TASKS

async def tasks_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process task completion and request wallet"""
    user = update.effective_user
    user_input = update.message.text.lower()
    
    # Only respond to "done" command
    if "done" not in user_input:
        await update.message.reply_text(
            "Please complete the tasks and send 'done' when finished.",
            reply_markup=create_task_keyboard()
        )
        return TASKS
    
    # Acknowledge task completion
    await update.message.reply_text(
        "Well done! Hope you didn't cheat the system 😏\n\n"
        "📬 Now, send me your **Ethereum wallet address** to receive your NFT:",
        parse_mode="Markdown"
    )
    return WALLET

async def receive_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process wallet address and complete the flow"""
    user = update.effective_user
    wallet = update.message.text
    
    # Add user to completed set
    completed_users.add(user.id)
    
    # Send success messages
    await update.message.reply_text(
        f"🚀 Congratulations! Your exclusive Milmotif NFT is being transferred to:\n\n"
        f"`{wallet}`\n\n"
        "⏳ *The NFT will appear in your wallet shortly.*",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(
        "🌐 **Explore more of our collection on OpenSea:**\n"
        f"{OPENSEA_WEBSITE}\n\n"
        "🎉 **Congratulations, you've completed the Milmotif NFT Giveaway!**",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Allow users to exit the flow"""
    await update.message.reply_text("Giveaway canceled. Type /start to try again.")
    return ConversationHandler.END

async def handle_completed_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages from users who already completed the giveaway"""
    user = update.effective_user
    if user.id in completed_users:
        await update.message.reply_text(
            "🎉 You have completed the Milmotif NFT Giveaway. Thank you!",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    return None

def main() -> None:
    """Run the bot."""
    # Get token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN", "7549078984:AAEOOejeephT6gQzP0lSTYSpMYY9ZjWQ76c")
    
    # Create Application
    application = Application.builder().token(token).build()

    # Conversation handler for new users
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TASKS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    tasks_completed
                )
            ],
            WALLET: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, 
                    receive_wallet
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        map_to_parent={
            ConversationHandler.END: ConversationHandler.END
        }
    )

    # Handler for completed users
    completed_handler = MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_completed_user
    )

    application.add_handler(conv_handler)
    application.add_handler(completed_handler)

    # Check if running on Render
    if os.getenv("RENDER") or os.getenv("RENDER_EXTERNAL_HOSTNAME"):
        try:
            PORT = int(os.environ.get("PORT", 8443))
            service_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
            
            if service_url:
                # Auto-configure webhook URL
                WEBHOOK_URL = f"https://{service_url}/webhook"
                logger.info(f"Starting webhook on {WEBHOOK_URL}")
                
                # Start webhook server
                application.run_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    webhook_url=WEBHOOK_URL,
                    url_path="/webhook",
                    drop_pending_updates=True
                )
                return
        except Exception as e:
            logger.error(f"Webhook setup error: {e}")

    # Fallback to polling
    logger.info("Starting in polling mode...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
