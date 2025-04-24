import mysql.connector
from mysql.connector import Error
import os
import sys

# Añadir el directorio raíz al path para importar config.py de la raíz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ahora importará desde la raíz del proyecto
from config import DB_CONFIG

def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None