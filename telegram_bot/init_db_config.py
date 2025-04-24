import sys
import os
import mysql.connector

# Intentar importar directamente desde el archivo local
try:
    # Primero intentar importar del módulo local
    from config import TELEGRAM_TOKEN
    print(f"Token importado correctamente desde el archivo local")
except ImportError:
    print(f"No se pudo importar el token desde el archivo local")
    sys.exit(1)

WELCOME_MESSAGE = "Bienvenido a Bogoker!"
HELP_MESSAGE = "Puedo ayudarte a encontrar propiedades."
FINISH_MESSAGE = "Gracias por contactarnos."

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="bogoker"
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def main():
    if not TELEGRAM_TOKEN:
        print("El token del bot no está configurado en config.py")
        return
        
    conn = get_connection()
    if not conn:
        print("No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SHOW TABLES LIKE 'bot_config'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            # Crear la tabla si no existe
            cursor.execute('''
                CREATE TABLE bot_config (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    bot_token VARCHAR(255) NOT NULL,
                    webhook_url VARCHAR(255),
                    welcome_message TEXT,
                    help_message TEXT,
                    finish_message TEXT,
                    update_interval INT DEFAULT 60,
                    auto_restart BOOLEAN DEFAULT TRUE,
                    log_conversations BOOLEAN DEFAULT TRUE,
                    notify_new_leads BOOLEAN DEFAULT FALSE,
                    notification_chat_id VARCHAR(100),
                    is_active BOOLEAN DEFAULT FALSE,
                    last_update DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("Tabla bot_config creada")
        
        # Verificar si ya hay un registro
        cursor.execute("SELECT COUNT(*) FROM bot_config")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insertar la configuración con el token
            cursor.execute('''
                INSERT INTO bot_config (
                    bot_token, welcome_message, help_message, finish_message
                ) VALUES (%s, %s, %s, %s)
            ''', (
                TELEGRAM_TOKEN, 
                WELCOME_MESSAGE, 
                HELP_MESSAGE, 
                FINISH_MESSAGE
            ))
            print("Token importado a la base de datos")
        else:
            # Actualizar el token existente
            cursor.execute('''
                UPDATE bot_config
                SET bot_token = %s, 
                    welcome_message = %s,
                    help_message = %s,
                    finish_message = %s
                WHERE id = 1
            ''', (TELEGRAM_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE, FINISH_MESSAGE))
            print("Token y mensajes actualizados en la base de datos")
        
        conn.commit()
        
        # Verificar la tabla de logs
        cursor.execute("SHOW TABLES LIKE 'bot_logs'")
        logs_table_exists = cursor.fetchone()
        
        if not logs_table_exists:
            cursor.execute('''
                CREATE TABLE bot_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level VARCHAR(20) NOT NULL,
                    message TEXT NOT NULL
                )
            ''')
            print("Tabla bot_logs creada")
            
            # Añadir un registro inicial
            cursor.execute(
                "INSERT INTO bot_logs (level, message) VALUES (%s, %s)",
                ('INFO', 'Configuración inicializada con token desde config.py')
            )
            conn.commit()
            
        print("¡Inicialización completada con éxito!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()