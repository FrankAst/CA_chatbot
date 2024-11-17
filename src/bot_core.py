# CHATBOT 0.0.1

########################### Libraries and config ###########################

# Packages:
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (filters, MessageHandler, Application,
                          CommandHandler, CallbackQueryHandler, ContextTypes,
                          ConversationHandler)
import data_validation as dv
import rag as rg
import time
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
search_flag = 0 # Nos permite buscar solo por provincia cuando no encuentra departamento y localidad

QT, QNA, PROV, DEPTO, LOCAL, BUSQUEDA = range(6)

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
        response_text = "Quisiera realizarle alguna pregunta tecnica a nuestro bot? De lo contrario tipea /next."
        query_type = "DTM"
    
    await query.edit_message_text(text=response_text)
    logger.info("User %s selected option %s", query.from_user.username, query.data)
    
    if query_type == "DTM":
        logger.info("Transitioning to QNA state")
        return QNA
    
    logger.info("Transitioning to PROV state")
    
    return PROV

# Q&A DTM Handler
async def qna_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    
    if len(user_query) <= 2: # Caso que el cliente responde: si
        await update.message.reply_text("Por favor indique su pregunta.")
        return QNA
    
    logging.info("Iniciando RAG ..")
    
    # Pasamos la query al rag:
    response = rg.rag(user_query)
    await update.message.reply_text(response)
    return QNA

# Transition handler
async def next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    logging.info("Transicionando a PROV")
    await update.message.reply_text("Perfecto, indique su provincia:")
    return PROV

# Provincia handler
async def province_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    logger.info("PROV state started")
    
    global provincia, query_type, search_flag
    
    input = update.message.text
    
    # check input with Abel's function.
    provincia = dv.val(input, 'Provincia', query_type)
    
    logger.info(f"Provincia de {update.message.from_user.username}: {provincia} ") 
    
    if provincia == 'CIUDAD AUTONOMA DE BUENOS AIRES':
        await update.message.reply_text("Buscando..")
        return await buscar_rep(update, context)
    
    await update.message.reply_text(
        f"Perfecto, por favor digame en que departamento de {input}"
        " se encuentra."
    )
    
    return DEPTO
 
# Departamento handler
async def depto_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    global departamento,provincia, query_type
    
    input = update.message.text
    # check input with Abel's function.
    departamento = dv.val(input, 'Departamento / Partido', query_type, provincia)
    
    logger.info(f"Departamento de {update.message.from_user.username}: {departamento} ") 
    
    if departamento == 'CIUDAD AUTONOMA DE BUENOS AIRES':
        departamento = None # limpiamos la variable
        provincia = 'CIUDAD AUTONOMA DE BUENOS AIRES' # reasignamos provincia y buscamos.
        await update.message.reply_text("Buscando..")
        return await buscar_rep(update, context)
    
    await update.message.reply_text(
        f"Y finalmente, necesitaria saber en que localidad de {input}"
        " se encuentra."
    )
    
    return LOCAL

# Departamento handler
async def local_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    
    global localidad, query_type
    
    input = update.message.text
    # check input with Abel's function.
    localidad = dv.val(input, 'localidad', query_type, provincia)
    
    logger.info(f"Departamento de {update.message.from_user.username}: {localidad} ") 
    
    await update.message.reply_text(
        f"Muchas gracias, dejeme buscarle el mejor representante..."
    )
    time.sleep(0.5)
    
    return await buscar_rep(update, context)

    

async def buscar_rep(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    global provincia, departamento, localidad, query_type, search_flag
    
    
    # Perform the search - si search_flag = 1 es porque no encontro resultados usando depto y localidad
    if search_flag == 0:
            results = dv.search(query_type, provincia, departamento, localidad)
    else:   results = dv.search(query_type, provincia)
    
    # Chequeamos que haya resultados
    if results is not None and results.shape[0] > 0:
        
        results = results[~results['Nombre'].duplicated(keep="first")]
        
        # Iniciamos el mensaje de respuesta
        final_message = "Pruebe comunicarse con: \n\n"
        result_count = len(results)
        
        # Fijamos un maximo de salidas
        max_results = 4
        display_count = min(result_count, max_results)
        
        # Iteramos sobre los resultados y acumulamos texto:
        for idx, row in results.head(display_count).iterrows():
            
            # Guardamos los datos, o 'No disponible' si no estan vacios
            nombre = row.get('Nombre', 'No disponible')
            email = row.get('e-Mail', 'No disponible')
            celular = row.get('Celular', 'No disponible')
            
            # Creamos msj
            message = (
                f"Nombre: {nombre}\n"
                f"Email: {email}\n"
                f"Celular: {celular}\n"
                "-----------------------------\n\n"
                
            )
                
            # Unimos mensaje final
            final_message += message
        
        saludo = "Para volver consultar clickee /start o para salir /cancel"
        final_message += saludo
        
        # Enviamos mensaje
        await update.message.reply_text(final_message)
    
    else: 
        # Chequeamos el flag:
        if search_flag == 0:
            search_flag = 1
        else: # Si no se encontraron resultados buscando solo con provincia, le avisamos que no hay representantes en su zona.
            await update.message.reply_text("Lo siento, no tenemos nadie en el área que coincida con su búsqueda. \n"
                                        "Clickee /start para realizar otra consulta o /cancel para salir")
    
    # Vaciamos las variables
    provincia = None
    departamento = None
    localidad = None
    query_type = None
    search_flag = 0
    
    # fin
    return ConversationHandler.END


# Salir de la conversacion
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    user = update.message.from_user
    logger.info("Usuario %s ha cancelado la conversacion.", user.first_name)
    await update.message.reply_text(
        "Adios! Muchas gracias por su consulta."
    )


    # Vaciamos las variables
    provincia = None
    departamento = None
    localidad = None
    query_type = None
    search_flag = 0
    
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
                    QNA:[
                        MessageHandler(filters.TEXT & (~filters.COMMAND), qna_handler),
                        CommandHandler("next", next)],
                    PROV: [MessageHandler(filters.TEXT & (~filters.COMMAND), province_ask)],
                    DEPTO: [MessageHandler(filters.TEXT & (~filters.COMMAND), depto_ask)],
                    LOCAL: [MessageHandler(filters.TEXT & (~filters.COMMAND), local_ask)]
                    
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
    
    
