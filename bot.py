import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
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
NFT_COLLECTION = "https://milmotif.com/milmotif/from-concept-to-nft-the-digital-design-journey-of-milmotif/"
TELEGRAM_GROUP = "https://t.me/milmotifgroup"
TWITTER_PROFILE = "https://x.com/milmotif"
OPENSEA_GALLERY = "https://opensea.io/milmotifart/galleries"
OPENSEA_WEBSITE = "https://opensea.io/milmotifart"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send instructions and set initial state."""
    user = update.effective_user
    welcome_msg = (
        f"🌟 Welcome {user.first_name} to the Official Milmotif NFT Giveaway! 🌟\n\n"
        "🎨 **Discover Our Collection:**\n"
        f"{NFT_COLLECTION}\n\n"
        "📋 **To participate, please complete these simple tasks:**\n"
        f"1. Join our Telegram Group: {TELEGRAM_GROUP}\n"
        f"2. Follow us on Twitter: {TWITTER_PROFILE}\n"
        f"3. Visit our OpenSea Gallery: {OPENSEA_GALLERY}\n\n"
        "After completing the tasks, send any message to continue."
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", disable_web_page_preview=True)
    return TASKS

async def tasks_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Acknowledge tasks and request wallet address."""
    await update.message.reply_text("Well done! Hope you didn't cheat the system 😏")
    await update.message.reply_text(
        "📬 Now, send me your **Ethereum wallet address** to receive your NFT:",
        parse_mode="Markdown"
    )
    return WALLET

async def receive_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process wallet address and send final messages."""
    wallet = update.message.text
    response = (
        f"🚀 Congratulations! Your exclusive Milmotif NFT is being transferred to your wallet.\n\n"
        f"`{wallet}`\n\n"
        "⏳ *The NFT will appear in your wallet shortly.*\n\n"
        "🌐 **Explore more of our collection on OpenSea:**\n"
        f"{OPENSEA_WEBSITE}\n\n"
        "🎉 **Congratulations, you've completed the Milmotif NFT Giveaway!**"
    )
    await update.message.reply_text(response, parse_mode="Markdown", disable_web_page_preview=True)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Allow users to exit the flow."""
    await update.message.reply_text("Giveaway canceled. Type /start to try again.")
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Get token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN", "7549078984:AAEOOejeephT6gQzP0lSTYSpMYY9ZjWQ76c")
    
    # Create Application
    application = Application.builder().token(token).build()

    # Set up conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TASKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tasks_completed)],
            WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_wallet)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Check if running on Render
    if os.getenv("RENDER") or os.getenv("RENDER_EXTERNAL_HOSTNAME"):
        PORT = int(os.environ.get("PORT", 8443))
        service_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
        
        if service_url:
            # Auto-configure webhook URL
            WEBHOOK_URL = f"https://{service_url}/webhook"
            
            # Start webhook server
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=WEBHOOK_URL,
                url_path="/webhook",
                drop_pending_updates=True
            )
            return
        
        logging.warning("RENDER_EXTERNAL_HOSTNAME not found, falling back to polling")

    # Local development (polling)
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
