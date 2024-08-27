# CHATBOT 0.0.1

########################### Libraries and config ###########################

# Packages:
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackQueryHandler, ContextTypes

from datetime import datetime, timedelta

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

directory = Path(__file__).resolve()
config_path = directory.parent.parent 

sys.path.append(str(config_path)+ "/config/")

try:
    import cfg 
except ImportError as e:
    logger.error("Fallo importar la configuracion: %s",e)
    sys.exit("Revisar el modulo cfg - revisar si el PATH esta correcto")


########################### GLOBAL VARIALBES ###########################

# Storing timestamp of the last /start command
last_start_time = None

# User data
query_type = None #RTV or DTM
province = None



########################### BOT FUNCTIONS ###########################

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    global last_start_time
    last_start_time = datetime.now()
    
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                   text="Bienvenido, por favor indique el motivo de asistencia:")
    
    keyboard = [
        [InlineKeyboardButton("Asistencia comercial", callback_data='1')],
        [InlineKeyboardButton("Asistencia tecnica", callback_data='2')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Elija una opcion', reply_markup=reply_markup)
    logger.info("Start command invoked by user: %s", update.message.from_user.username)
    
# Echo handler  - Indica al usuario como iniciar el bot.
async def echo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    global last_start_time
    
    if last_start_time is None or datetime.now() - last_start_time > timedelta(minutes=5):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Por favor ingresar /start para usar el bot.")
    else:
        pass
    

# Button callback handler - Primer filtro. 
async def query_type_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    global query_type
    
    query = update.callback_query
    await query.answer()

    if query.data == '1':
        response_text = "Bienvenido"
        query_type = "RTV"
    elif query.data == '2':
        response_text = "Bienvenido"
        query_type = "DTM"
    else:
        response_text = "Seleccion no valida"

    await query.edit_message_text(text=response_text)
    logger.info("User %s selected option %s", query.from_user.username, query.data)
    
# 
#async def province_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    






















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
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo_start))
        
        
        application.add_handler(CallbackQueryHandler(query_type_button))
        
        
        
        
        application.add_error_handler(error_handler)
        

        # Start the Bot using run_polling
        application.run_polling()

    except Exception as e:
        logger.critical("An exception occurred: %s", e)
        sys.exit("An exception occurred. Exiting...")
    
    
