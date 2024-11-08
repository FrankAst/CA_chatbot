import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, InlineQueryHandler
from uuid import uuid4


#Set up logging

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
    
TOKEN = cfg.TOKEN_BOT

########################### BOT FUNCTIONS ###########################


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")
    
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id=str(uuid4()),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)





########################### BOT EXEC ###########################

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler('caps', caps)
    inline_caps_handler = InlineQueryHandler(inline_caps)
    
    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(caps_handler)
    application.add_handler(inline_caps_handler)
    
    application.run_polling()