# CHATBOT 0.0.1
# la amiguita de ayer
########################### Libraries and config ###########################

# Packages:
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (filters, MessageHandler, Application,
                          CommandHandler, CallbackQueryHandler, ContextTypes,
                          ConversationHandler)

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
provincia = None
departamento = None
localidad = None

QT, PROV, DEPTO, LOCAL, BUSQUEDA = range(5)

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
    
    return QT
    
# Echo handler  - Indica al usuario como iniciar el bot.
async def echo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    global last_start_time
    
    if last_start_time is None or datetime.now() - last_start_time > timedelta(minutes=5):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Por favor ingresar /start para usar el bot.")
    else:
        pass
    

# Button callback handler - Primer filtro. 
async def query_type_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    global query_type
    
    query = update.callback_query
    await query.answer()

    if query.data == '1':
        response_text = "Para contactarlo con un tecnico de ventas, necesitaremos que nos indique en que provincia se halla:"
        query_type = "RTV"
    else: #query.data == '2'
        response_text = "Para contactarlo con un delegado tecnico de mercado, necesitaremos que nos indique en que provincia se halla:"
        query_type = "DTM"
    
    await query.edit_message_text(text=response_text)
    logger.info("User %s selected option %s", query.from_user.username, query.data)
    
    logger.info("Transitioning to PROV state")
    
    return PROV
    
# Provincia handler
async def province_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    logger.info("PROV state started")
    
    global provincia
    
    input = update.message.text
    
    # check input with Abel's function.
    # provincia = funcion_abel(input)
    
    logger.info(f"Provincia de {update.message.from_user.username}: {input} ") #reemplazar input con provincia
    
    await update.message.reply_text(
        f"Perfecto, por favor digame en que departamento de {input},"
        "se encuentra."
    )
    
    return DEPTO
 
# Departamento handler
async def depto_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    global departamento
    
    input = update.message.text
    # check input with Abel's function.
    # departamento = funcion_abel(input)
    
    logger.info(f"Departamento de {update.message.from_user.username}: {input} ") #reemplazar input con departamento
    
    await update.message.reply_text(
        f"Y finalmente, necesitaria saber en que localidad de {input},"
        "se encuentra."
    )
    
    return LOCAL

# Departamento handler
async def local_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    global localidad
    
    input = update.message.text
    # check input with Abel's function.
    # localidad = funcion_abel(input)
    
    logger.info(f"Departamento de {update.message.from_user.username}: {input} ") #reemplazar input con localidad
    
    await update.message.reply_text(
        f"Muchas gracias, dejeme buscarle el mejor representante."
    )
    
    return BUSQUEDA
    
# Busqueda handler
async def buscar_rep(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    
    global provincia, departamento, localidad
    
    await update.message.reply_text(
        f"Pruebe comunicarse con Franco, el mejor representante en:"
        f"{localidad},{departamento},{provincia}. Muchas gracias!"
    )
    
    return ConversationHandler.END

# Salir de la conversacion
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    user = update.message.from_user
    logger.info("Usuario %s ha cancelado la conversacion.", user.first_name)
    await update.message.reply_text(
        "Adios! Muchas gracias por su consulta."
    )

    return ConversationHandler.END


# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)



########################### BOT EXEC ###########################

if __name__ == '__main__':
    
    try:
        # Initialize Application
        application = Application.builder().token(cfg.TOKEN_BOT).build()

        # Conversation handler build
        conv_handler = ConversationHandler(
            entry_points = [CommandHandler("start", start)],
            states = {
                    QT: [CallbackQueryHandler(query_type_button)],
                    PROV: [MessageHandler(filters.TEXT & (~filters.COMMAND), province_ask)],
                    DEPTO: [MessageHandler(filters.TEXT & (~filters.COMMAND), depto_ask)],
                    LOCAL: [MessageHandler(filters.TEXT & (~filters.COMMAND), local_ask)],
                    BUSQUEDA: [MessageHandler(filters.TEXT & (~filters.COMMAND), buscar_rep)]
                    
            },
            fallbacks = [CommandHandler("cancel", cancel)]
            
        )
        
        # Register command and callback handlers
        #application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo_start))
        application.add_handler(conv_handler)
    
        # Error handling
        application.add_error_handler(error_handler)
        

        # Start the Bot using run_polling
        application.run_polling()

    except Exception as e:
        logger.critical("An exception occurred: %s", e)
        sys.exit("An exception occurred. Exiting...")
    
    
