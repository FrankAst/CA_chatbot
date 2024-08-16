# CHATBOT 0.0.1

########################### Libraries and config ###########################

# Packages:
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# Set up logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Loading config file:
import sys
from pathlib import Path

# set path
directory = Path(__file__).resolve()
config_path = directory.parent.parent 
#print(str(config_path)+ "/config")

sys.path.append(str(config_path)+ "/config/")

try:
    import cfg 
except ImportError as e:
    logger.error("Fallo importar la configuracion: %s",e)
    sys.exit("Revisar el modulo cfg - revisar si el PATH esta correcto")



########################### BOT FUNCTIONS ###########################

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Option 1", callback_data='1')],
        [InlineKeyboardButton("Option 2", callback_data='2')],
        [InlineKeyboardButton("Option 3", callback_data='3')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose:', reply_markup=reply_markup)
    logger.info("Start command invoked by user: %s", update.message.from_user.username)

# Button callback handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == '1':
        response_text = "You selected option 1"
    elif query.data == '2':
        response_text = "You selected option 2"
    elif query.data == '3':
        response_text = "You selected option 3"
    else:
        response_text = "Invalid selection"

    await query.edit_message_text(text=response_text)
    logger.info("User %s selected option %s", query.from_user.username, query.data)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)



########################### BOT EXEC ###########################


if __name__ == '__main__':
    
    try:
        # Initialize Application
        application = Application.builder().token(cfg.TOKEN_BOT).build()

        # Register command and callback handlers
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_error_handler(error_handler)

        # Start the Bot using run_polling
        print("line 85 - about to run_polling")
        application.run_polling()

    except Exception as e:
        logger.critical("An exception occurred: %s", e)
        sys.exit("An exception occurred. Exiting...")
    
    
