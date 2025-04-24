from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from .models import User
from database.db_connection import get_connection

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    nombre_usuario = request.form.get('nombre_usuario')
    contraseña = request.form.get('contraseña')
    remember = True if request.form.get('remember') else False
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s AND contraseña = %s", 
                           (nombre_usuario, contraseña))
            user_data = cursor.fetchone()
            
            if user_data:
                user = User(
                    id_usuario=user_data['id_usuario'],
                    nombre_usuario=user_data['nombre_usuario'],
                    correo=user_data['correo'],
                    rol=user_data['rol']
                )
                login_user(user, remember=remember)
                return redirect(url_for('main.dashboard'))
        finally:
            conn.close()
    
    flash('Por favor, revisa tus credenciales e intenta de nuevo.')
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))