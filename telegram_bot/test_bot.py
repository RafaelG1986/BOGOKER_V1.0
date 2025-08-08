#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

print("Importing telegram...")
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove

print("Importing telegram.ext...")
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters,
)

print("Importing config...")
try:
    from config import TELEGRAM_TOKEN
except ImportError:
    print("Error: No se pudo importar TELEGRAM_TOKEN")
    sys.exit(1)

print("Creating Application...")
try:
    application = Application.builder().token(TELEGRAM_TOKEN).job_queue(None).build()
    print("¡Application creada exitosamente!")
except Exception as e:
    print(f"Error al crear Application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("¡Test exitoso! El bot básico funciona.")
