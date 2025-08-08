import os
import sys
import logging
import signal
import mysql.connector
from datetime import datetime
import pytz

try:
    import imghdr
except ImportError:
    # Crear un módulo falso para imghdr
    import sys
    from types import ModuleType
    
    imghdr = ModuleType('imghdr')
    imghdr.what = lambda file, h=None: None
    sys.modules['imghdr'] = imghdr
    print("Usando implementación falsa de imghdr")

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters,
)

# Importar configuración
try:
    from config import TELEGRAM_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE, FINISH_MESSAGE
except ImportError:
    # Valores por defecto si no se puede importar
    TELEGRAM_TOKEN = ""
    WELCOME_MESSAGE = "¡Bienvenido a Bogoker! Estamos aquí para ayudarte."
    HELP_MESSAGE = "Puedo ayudarte a encontrar propiedades."
    FINISH_MESSAGE = "Gracias por contactarnos."

# Configurar logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.log')
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Estados de la conversación
POLICY, LOCATION_CITY, LOCATION_ZONE, LOCATION_DEPARTMENT, PROPERTY_ADDRESS = range(5)
PROPERTY_TYPE, PROPERTY_CONDITION, PROPERTY_VALUE = range(5, 8)
CONTACT_NAME, CONTACT_LASTNAME, CONTACT_ID, CONTACT_EMAIL = range(8, 12)
CONTACT_PHONE, CONTACT_CELLPHONE, CONTACT_WHATSAPP = range(12, 15)

# Almacenamiento de datos de usuario
user_data_dict = {}

# Función para obtener conexión a la base de datos
def get_connection():
    try:
        # Intentar obtener la configuración desde el módulo
        DB_CONFIG = {
            "host": "localhost",
            "database": "bogoker",
            "user": "root",
            "password": ""
        }
        
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return None

# Manejador de señales para terminación limpia
def signal_handler(sig, frame):
    """Maneja la señal de terminación."""
    logger.info("Recibida señal de terminación. Deteniendo el bot...")
    
    # Eliminar archivo PID
    pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.pid')
    if os.path.exists(pid_file):
        os.remove(pid_file)
        logger.info("Archivo PID eliminado")
    
    # Salir limpiamente
    sys.exit(0)

# Registrar el manejador de señales
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def start(update: Update, context: CallbackContext) -> int:
    """Inicia la conversación y solicita aceptación de política."""
    user = update.effective_user
    logger.info(f"Usuario {user.id} ({user.first_name}) inició una conversación")
    
    # Inicializar datos del usuario
    user_data_dict[user.id] = {}
    user_data_dict[user.id]["telegram_id"] = user.id
    user_data_dict[user.id]["telegram_username"] = user.username
    
    await update.message.reply_text(
        f"{WELCOME_MESSAGE}\n\n"
        "Para comenzar, necesitamos que aceptes nuestra política de protección de datos personales.\n"
        "Escribe 'Acepto' para continuar."
    )
    return POLICY

async def policy(update: Update, context: CallbackContext) -> int:
    """Procesa la respuesta de la política y solicita ubicación."""
    user = update.effective_user
    text = update.message.text
    
    if text.lower() != "acepto":
        await update.message.reply_text(
            "Debes aceptar nuestra política de protección de datos para continuar.\n"
            "Escribe 'Acepto' para continuar o /cancel para salir."
        )
        return POLICY
    
    user_data_dict[user.id]["acepta_politica"] = True
    user_data_dict[user.id]["fecha_registro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    await update.message.reply_text(
        "¡Gracias por aceptar nuestra política!\n\n"
        "Ahora, necesitamos algunos datos sobre la propiedad.\n"
        "¿En qué ciudad está ubicada la propiedad?"
    )
    return LOCATION_CITY

async def location_city(update: Update, context: CallbackContext) -> int:
    """Guarda la ciudad y solicita la zona."""
    user = update.effective_user
    ciudad = update.message.text
    user_data_dict[user.id]["ciudad"] = ciudad
    
    await update.message.reply_text(f"¿En qué zona/localidad/ubicación de {ciudad} te encuentras?")
    return LOCATION_ZONE

async def location_zone(update: Update, context: CallbackContext) -> int:
    """Guarda la zona y solicita el departamento."""
    user = update.effective_user
    user_data_dict[user.id]["zona"] = update.message.text
    
    await update.message.reply_text("¿En qué estado/departamento te encuentras?")
    return LOCATION_DEPARTMENT

async def location_department(update: Update, context: CallbackContext) -> int:
    """Guarda el departamento y solicita dirección."""
    user = update.effective_user
    user_data_dict[user.id]["departamento"] = update.message.text
    user_data_dict[user.id]["pais"] = "Colombia"
    
    await update.message.reply_text(
        "Ahora necesitamos información sobre la propiedad.\n\n"
        "Por favor, ingresa la dirección de la propiedad:"
    )
    return PROPERTY_ADDRESS

async def property_address(update: Update, context: CallbackContext) -> int:
    """Guarda la dirección y solicita tipo de propiedad."""
    user = update.effective_user
    user_data_dict[user.id]["direccion"] = update.message.text
    
    keyboard = [
        ["Casa", "Apartamento"],
        ["Local comercial", "Oficina"],
        ["Lote", "Bodega"],
        ["Otro"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "¿Qué tipo de propiedad es?",
        reply_markup=reply_markup
    )
    return PROPERTY_TYPE

async def property_type(update: Update, context: CallbackContext) -> int:
    """Guarda el tipo de propiedad y solicita condición."""
    user = update.effective_user
    user_data_dict[user.id]["tipo_propiedad"] = update.message.text
    
    keyboard = [
        ["Excelente", "Buena"],
        ["Regular", "Necesita reparaciones"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    
    await update.message.reply_text(
        "¿En qué condición se encuentra la propiedad?",
        reply_markup=reply_markup
    )
    return PROPERTY_CONDITION

async def property_condition(update: Update, context: CallbackContext) -> int:
    """Guarda la condición y solicita valor."""
    user = update.effective_user
    user_data_dict[user.id]["condicion"] = update.message.text
    
    await update.message.reply_text(
        "¿Cuál es el valor aproximado de la propiedad? (en pesos colombianos)"
    )
    return PROPERTY_VALUE

async def property_value(update: Update, context: CallbackContext) -> int:
    """Guarda el valor y solicita información de contacto."""
    user = update.effective_user
    user_data_dict[user.id]["valor"] = update.message.text
    
    await update.message.reply_text(
        "¡Genial! Ahora necesitamos algunos datos personales para contactarte.\n\n"
        "¿Cuál es tu nombre?",
        reply_markup=ReplyKeyboardRemove()
    )
    return CONTACT_NAME

async def contact_name(update: Update, context: CallbackContext) -> int:
    """Guarda el nombre y solicita apellido."""
    user = update.effective_user
    user_data_dict[user.id]["nombre"] = update.message.text
    
    await update.message.reply_text("¿Cuál es tu apellido?")
    return CONTACT_LASTNAME

async def contact_lastname(update: Update, context: CallbackContext) -> int:
    """Guarda el apellido y solicita número de identificación."""
    user = update.effective_user
    user_data_dict[user.id]["apellido"] = update.message.text
    
    await update.message.reply_text("¿Cuál es tu número de identificación?")
    return CONTACT_ID

async def contact_id(update: Update, context: CallbackContext) -> int:
    """Guarda la identificación y solicita email."""
    user = update.effective_user
    user_data_dict[user.id]["identificacion"] = update.message.text
    
    await update.message.reply_text("¿Cuál es tu correo electrónico?")
    return CONTACT_EMAIL

async def contact_email(update: Update, context: CallbackContext) -> int:
    """Guarda el email y solicita teléfono fijo."""
    user = update.effective_user
    user_data_dict[user.id]["email"] = update.message.text
    
    await update.message.reply_text(
        "¿Cuál es tu número de teléfono fijo? (Si no tienes, escribe 'No tengo')"
    )
    return CONTACT_PHONE

async def contact_phone(update: Update, context: CallbackContext) -> int:
    """Guarda el teléfono fijo y solicita celular."""
    user = update.effective_user
    user_data_dict[user.id]["telefono"] = update.message.text
    
    await update.message.reply_text("¿Cuál es tu número de celular?")
    return CONTACT_CELLPHONE

async def contact_cellphone(update: Update, context: CallbackContext) -> int:
    """Guarda el celular y solicita whatsapp."""
    user = update.effective_user
    user_data_dict[user.id]["celular"] = update.message.text
    
    await update.message.reply_text(
        "¿Tienes WhatsApp en este número? (Sí/No)",
        reply_markup=ReplyKeyboardMarkup([
            ["Sí"], 
            ["No"]
        ], one_time_keyboard=True),
    )
    return CONTACT_WHATSAPP

async def contact_whatsapp(update: Update, context: CallbackContext) -> int:
    """Guarda si tiene whatsapp y finaliza la conversación."""
    user = update.effective_user
    user_data_dict[user.id]["whatsapp"] = update.message.text.lower() == "sí"
    
    # Guardar datos en la base de datos
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Iniciar transacción
            conn.start_transaction()
            
            # 1. Primero insertar ubicación
            cursor.execute("""
                INSERT INTO ubicaciones (ciudad, zona, departamento, pais)
                VALUES (%s, %s, %s, %s)
            """, (
                user_data_dict[user.id].get("ciudad", ""),
                user_data_dict[user.id].get("zona", ""),
                user_data_dict[user.id].get("departamento", ""),
                user_data_dict[user.id].get("pais", "Colombia")
            ))
            id_ubicacion = cursor.lastrowid
            
            # 2. Insertar lead básico
            cursor.execute("""
                INSERT INTO leads (origen, chat_id, fecha_creacion, archivado) 
                VALUES (%s, %s, NOW(), 0)
            """, (
                "Telegram Bot",
                user_data_dict[user.id].get("telegram_id", "")
            ))
            lead_id = cursor.lastrowid
            
            # 3. Insertar contacto
            cursor.execute("""
                INSERT INTO contactos (
                    id_lead, nombre, apellido, numero_identificacion, 
                    correo, telefono, celular, whatsapp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lead_id,
                user_data_dict[user.id].get("nombre", ""),
                user_data_dict[user.id].get("apellido", ""),
                user_data_dict[user.id].get("identificacion", ""),
                user_data_dict[user.id].get("email", ""),
                user_data_dict[user.id].get("telefono", ""),
                user_data_dict[user.id].get("celular", ""),
                user_data_dict[user.id].get("whatsapp", False)
            ))
            
            # 4. Insertar propiedad
            cursor.execute("""
                INSERT INTO propiedades (
                    id_lead, id_ubicacion, tipo, condicion, direccion, valor
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                lead_id,
                id_ubicacion,
                user_data_dict[user.id].get("tipo_propiedad", ""),
                user_data_dict[user.id].get("condicion", ""),
                user_data_dict[user.id].get("direccion", ""),
                user_data_dict[user.id].get("valor", "")
            ))
            
            # Confirmar todos los cambios
            conn.commit()
            
            logger.info(f"Lead guardado con ID: {lead_id}")
            
            # Limpiar datos del usuario
            del user_data_dict[user.id]
            
            await update.message.reply_text(
                f"{FINISH_MESSAGE}\n\n"
                "Hemos registrado tu información correctamente. Un asesor se pondrá en contacto contigo a la brevedad.\n\n"
                "Si necesitas algo más, puedes escribir /start para comenzar una nueva consulta.",
                reply_markup=ReplyKeyboardRemove()
            )
            
        except Exception as e:
            logger.error(f"Error al guardar lead: {e}")
            conn.rollback()
            
            try:
                # Guardar el error detallado en un archivo para revisión
                with open('error_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\n[{datetime.now()}] Error en user_id {user.id}:\n")
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"Datos: {str(user_data_dict[user.id])}\n")
                    f.write("-" * 50 + "\n")
            except:
                pass  # Asegurar que esto no cause otro error
            
            await update.message.reply_text(
                "Lo sentimos, ha ocurrido un error al procesar tu información.\n"
                "Por favor, intenta nuevamente más tarde o contacta directamente con nosotros.\n\n"
                "Puedes escribir /start para comenzar una nueva consulta.",
                reply_markup=ReplyKeyboardRemove()
            )
        finally:
            conn.close()
    else:
        # Error de conexión a la BD
        await update.message.reply_text(
            "Lo sentimos, no pudimos conectarnos a nuestra base de datos.\n"
            "Por favor, intenta nuevamente más tarde o contacta directamente con nosotros.\n\n"
            "Puedes escribir /start para comenzar una nueva consulta.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """Cancela la conversación."""
    user = update.effective_user
    
    # Limpiar datos si existen
    if user.id in user_data_dict:
        del user_data_dict[user.id]
    
    await update.message.reply_text(
        "Has cancelado la operación. Si deseas comenzar de nuevo, escribe /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END

async def help_command(update: Update, context: CallbackContext) -> None:
    """Envía un mensaje cuando se emite el comando /help."""
    await update.message.reply_text(HELP_MESSAGE)

async def echo(update: Update, context: CallbackContext) -> None:
    """Echo para debugging."""
    # Guardar mensaje para debug
    with open('debug_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"Mensaje recibido de {update.effective_user.id}: {update.message.text}\n")
    
    await update.message.reply_text(
        "Para comenzar una consulta, por favor escribe /start"
    )

def main():
    """Inicia el bot."""
    # Guardar el PID para que la web pueda controlar el proceso
    pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.pid')
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Log de inicio
    logger.info(f"Bot iniciado con PID {os.getpid()}")
    
    # Crear la aplicación SIN JobQueue para evitar problemas de timezone en Windows
    application = Application.builder().token(TELEGRAM_TOKEN).job_queue(None).build()

    # Añadir manejador de conversación
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            POLICY: [MessageHandler(filters.TEXT & ~filters.COMMAND, policy)],
            LOCATION_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_city)],
            LOCATION_ZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_zone)],
            LOCATION_DEPARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, location_department)],
            PROPERTY_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, property_address)],
            PROPERTY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, property_type)],
            PROPERTY_CONDITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, property_condition)],
            PROPERTY_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, property_value)],
            CONTACT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_name)],
            CONTACT_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_lastname)],
            CONTACT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_id)],
            CONTACT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_email)],
            CONTACT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_phone)],
            CONTACT_CELLPHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_cellphone)],
            CONTACT_WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_whatsapp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Añadir otros manejadores
    application.add_handler(CommandHandler("help", help_command))
    
    # Manejador por defecto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Iniciar el bot
    logger.info(f"Bot escuchando. Usa Ctrl+C para detener.")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()