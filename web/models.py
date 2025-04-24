from flask_login import UserMixin
from database.db_connection import get_connection

class User(UserMixin):
    def __init__(self, id_usuario, nombre_usuario, correo, rol):
        self.id = id_usuario  # Flask-Login usa .id, así que mantenemos la compatibilidad
        self.id_usuario = id_usuario
        self.nombre_usuario = nombre_usuario
        self.correo = correo
        self.rol = rol
    
    @staticmethod
    def get(user_id):
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
            
            return User(
                id_usuario=user_data['id_usuario'],
                nombre_usuario=user_data['nombre_usuario'],
                correo=user_data['correo'],
                rol=user_data['rol']
            )
        finally:
            conn.close()
    
    @staticmethod
    def get_by_username(nombre_usuario):
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s", (nombre_usuario,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
            
            return User(
                id_usuario=user_data['id_usuario'],
                nombre_usuario=user_data['nombre_usuario'],
                correo=user_data['correo'],
                rol=user_data['rol']
            )
        finally:
            conn.close()
    
    @staticmethod
    def get_by_email(correo):
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
            
            return User(
                id_usuario=user_data['id_usuario'],
                nombre_usuario=user_data['nombre_usuario'],
                correo=user_data['correo'],
                rol=user_data['rol']
            )
        finally:
            conn.close()