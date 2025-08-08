from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
from database.db_connection import get_connection
import pandas as pd
import tempfile
import os
import subprocess
import json
import requests
from datetime import datetime
import signal
import sys
import time

try:
    from config import TELEGRAM_TOKEN, WELCOME_MESSAGE, HELP_MESSAGE, FINISH_MESSAGE
except ImportError:
    # Fallback para valores por defecto
    TELEGRAM_TOKEN = ""
    WELCOME_MESSAGE = "¡Bienvenido a Bogoker!"
    HELP_MESSAGE = "Puedo ayudarte a encontrar propiedades"
    FINISH_MESSAGE = "Gracias por contactarnos"

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Obtener leads de la base de datos
    leads = get_leads()
    
    # Obtener estadísticas para tarjetas informativas
    conn = get_connection()
    stats = {
        'total_leads': 0,
        'leads_activos': 0,
        'leads_hoy': 0,
        'leads_semana': 0
    }
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Total de leads
            cursor.execute("SELECT COUNT(*) as total FROM leads")
            stats['total_leads'] = cursor.fetchone()['total']
            
            # Leads activos (no archivados)
            cursor.execute("SELECT COUNT(*) as total FROM leads WHERE archivado = 0")
            stats['leads_activos'] = cursor.fetchone()['total']
            
            # Leads creados hoy
            cursor.execute("SELECT COUNT(*) as total FROM leads WHERE DATE(fecha_creacion) = CURDATE()")
            stats['leads_hoy'] = cursor.fetchone()['total']
            
            # Leads creados esta semana
            cursor.execute("SELECT COUNT(*) as total FROM leads WHERE fecha_creacion >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)")
            stats['leads_semana'] = cursor.fetchone()['total']
            
        finally:
            conn.close()
    
    return render_template('dashboard.html', leads=leads, 
                          total_leads=stats['total_leads'],
                          leads_activos=stats['leads_activos'],
                          leads_hoy=stats['leads_hoy'],
                          leads_semana=stats['leads_semana'])

@main.route('/dashboard/analytics')
@login_required
def analytics_dashboard():
    conn = get_connection()
    data = {
        'leads_por_mes': [],
        'tipos_propiedad': [],
        'leads_por_origen': [],
        'leads_por_ciudad': [],
        'valores_promedio': []
    }
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Leads por mes (últimos 12 meses)
        cursor.execute("""
            SELECT 
                DATE_FORMAT(fecha_creacion, '%Y-%m') as mes,
                COUNT(*) as cantidad
            FROM leads
            WHERE fecha_creacion >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY mes
            ORDER BY mes
        """)
        data['leads_por_mes'] = cursor.fetchall()
        
        # Tipos de propiedad
        cursor.execute("""
            SELECT tipo, COUNT(*) as cantidad 
            FROM propiedades 
            GROUP BY tipo 
            ORDER BY cantidad DESC
        """)
        data['tipos_propiedad'] = cursor.fetchall()
        
        # Leads por origen
        cursor.execute("""
            SELECT origen, COUNT(*) as cantidad 
            FROM leads 
            GROUP BY origen 
            ORDER BY cantidad DESC
        """)
        data['leads_por_origen'] = cursor.fetchall()
        
        # Valores promedio por ciudad
        cursor.execute("""
            SELECT u.ciudad, 
                   AVG(CAST(REPLACE(p.valor, '.', '') AS UNSIGNED)) as promedio,
                   COUNT(*) as cantidad
            FROM propiedades p
            JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
            GROUP BY u.ciudad
            HAVING COUNT(*) > 3
            ORDER BY promedio DESC
        """)
        data['valores_promedio'] = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error al cargar datos de análisis: {str(e)}', 'error')
    finally:
        conn.close()
    
    return render_template('dashboard/analytics.html', data=data)

@main.route('/lead/<int:lead_id>')
@login_required
def lead_detail(lead_id):
    lead = get_lead_by_id(lead_id)
    if not lead:
        flash('Lead no encontrado.')
        return redirect(url_for('main.dashboard'))
    return render_template('lead_detail.html', lead=lead)

@main.route('/lead/edit/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def edit_lead_old(lead_id):  # RENOMBRAR ESTA FUNCIÓN
    if request.method == 'POST':
        # Lógica para actualizar el lead
        update_lead(lead_id, request.form)
        flash('Lead actualizado correctamente.')
        return redirect(url_for('main.lead_detail', lead_id=lead_id))
    
    lead = get_lead_by_id(lead_id)
    if not lead:
        flash('Lead no encontrado.')
        return redirect(url_for('main.dashboard'))
    return render_template('edit_lead.html', lead=lead)

@main.route('/export/excel')
@login_required
def export_excel():
    leads = get_leads_for_export()
    
    # Convertir a DataFrame de pandas
    df = pd.DataFrame(leads)
    
    # Crear archivo temporal
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_filename = temp_file.name
    
    # Guardar a Excel
    df.to_excel(temp_filename, index=False)
    
    return send_file(
        temp_filename,
        as_attachment=True,
        download_name='leads_bogoker.xlsx',
        max_age=0
    )

@main.route('/export/<format>')
@login_required
def export_data(format):
    leads = get_leads_for_export()
    
    # Convertir a DataFrame de pandas
    df = pd.DataFrame(leads)
    
    if format == 'excel':
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_filename = temp_file.name
        
        # Guardar a Excel
        df.to_excel(temp_filename, index=False)
        
        return send_file(
            temp_filename,
            as_attachment=True,
            download_name='leads_bogoker.xlsx',
            max_age=0
        )
        
    elif format == 'csv':
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        temp_filename = temp_file.name
        
        # Guardar a CSV
        df.to_csv(temp_filename, index=False, encoding='utf-8-sig')  # Para soporte correcto de acentos
        
        return send_file(
            temp_filename,
            as_attachment=True,
            download_name='leads_bogoker.csv',
            max_age=0,
            mimetype='text/csv'
        )
        
    elif format == 'pdf':
        # Requiere instalar reportlab o similar
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_filename = temp_file.name
        
        # Crear documento PDF
        doc = SimpleDocTemplate(temp_filename, pagesize=letter)
        elements = []
        
        # Datos para la tabla
        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        
        # Generar PDF
        doc.build(elements)
        
        return send_file(
            temp_filename,
            as_attachment=True,
            download_name='leads_bogoker.pdf',
            max_age=0
        )
    
    else:
        flash(f'Formato de exportación no soportado: {format}', 'error')
        return redirect(url_for('main.dashboard'))

@main.route('/lead/<int:lead_id>/comentario', methods=['POST'])
@login_required
def add_comment(lead_id):
    comentario = request.form.get('comentario')
    if not comentario:
        flash('El comentario no puede estar vacío.', 'error')
        return redirect(url_for('main.lead_detail', lead_id=lead_id))
    
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comentarios (id_lead, id_usuario, comentario) VALUES (%s, %s, %s)",
                (lead_id, current_user.id_usuario, comentario)
            )
            conn.commit()
            flash('Comentario agregado con éxito', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error al agregar comentario: {str(e)}', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('main.lead_detail', lead_id=lead_id))

@main.route('/estadisticas')
@login_required
def estadisticas():
    conn = get_connection()
    stats = {}
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Total de leads
            cursor.execute("SELECT COUNT(*) as total FROM leads")
            stats['total_leads'] = cursor.fetchone()['total']
            
            # Leads por origen
            cursor.execute("SELECT origen, COUNT(*) as cantidad FROM leads GROUP BY origen ORDER BY cantidad DESC")
            stats['leads_por_origen'] = cursor.fetchall()
            
            # Leads por ciudad
            cursor.execute("""
                SELECT u.ciudad, COUNT(*) as cantidad 
                FROM leads l
                JOIN propiedades p ON l.id_lead = p.id_lead
                JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
                GROUP BY u.ciudad 
                ORDER BY cantidad DESC 
                LIMIT 10
            """)
            stats['leads_por_ciudad'] = cursor.fetchall()
            
            # Tipos de propiedad
            cursor.execute("""
                SELECT tipo, COUNT(*) as cantidad 
                FROM propiedades 
                GROUP BY tipo 
                ORDER BY cantidad DESC
            """)
            stats['tipos_propiedad'] = cursor.fetchall()
            
            # Valores promedio por tipo
            cursor.execute("""
                SELECT tipo, AVG(valor) as promedio 
                FROM propiedades 
                GROUP BY tipo 
                ORDER BY promedio DESC
            """)
            stats['valor_promedio'] = cursor.fetchall()
            
            # Leads por mes (últimos 6 meses)
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(fecha_creacion, '%Y-%m') as mes,
                    COUNT(*) as cantidad
                FROM leads
                WHERE fecha_creacion >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                GROUP BY mes
                ORDER BY mes
            """)
            stats['leads_por_mes'] = cursor.fetchall()
            
        finally:
            conn.close()
    
    return render_template('estadisticas.html', stats=stats)

def get_leads():
    conn = get_connection()
    leads = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT l.id_lead, l.fecha_creacion, l.archivado, l.origen, 
                       c.nombre, c.apellido, c.celular, c.correo, 
                       p.tipo, p.condicion, p.valor,
                       u.ciudad, u.zona, u.departamento,
                       (SELECT COUNT(*) FROM comentarios WHERE id_lead = l.id_lead) as num_comentarios
                FROM leads l
                LEFT JOIN contactos c ON l.id_lead = c.id_lead
                LEFT JOIN propiedades p ON l.id_lead = p.id_lead
                LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
                ORDER BY l.fecha_creacion DESC
            """
            cursor.execute(query)
            leads = cursor.fetchall()
        finally:
            conn.close()
    
    return leads

def get_lead_by_id(lead_id):
    conn = get_connection()
    lead = None
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT l.*, c.*, p.*, u.*
                FROM leads l
                LEFT JOIN contactos c ON l.id_lead = c.id_lead
                LEFT JOIN propiedades p ON l.id_lead = p.id_lead
                LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
                WHERE l.id_lead = %s
            """
            cursor.execute(query, (lead_id,))
            lead = cursor.fetchone()
            
            if lead:
                # Obtener comentarios
                cursor.execute("""
                    SELECT com.*, u.nombre_usuario 
                    FROM comentarios com
                    JOIN usuarios u ON com.id_usuario = u.id_usuario
                    WHERE com.id_lead = %s
                    ORDER BY com.fecha_creacion DESC
                """, (lead_id,))
                lead['comentarios'] = cursor.fetchall()
        finally:
            conn.close()
    
    return lead

def update_lead(lead_id, form_data):
    conn = get_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Actualizar lead (use archivado en lugar de estado)
            cursor.execute(
                "UPDATE leads SET archivado = %s WHERE id_lead = %s",
                (1 if form_data.get('archivar', False) else 0, lead_id)
            )
            
            # Actualizar contacto
            cursor.execute(
                """
                UPDATE contactos SET 
                nombre = %s, apellido = %s, correo = %s, 
                telefono = %s, celular = %s, whatsapp = %s
                WHERE id_lead = %s
                """,
                (
                    form_data['nombre'], form_data['apellido'], form_data['correo'],
                    form_data['telefono'], form_data['celular'], form_data['whatsapp'],
                    lead_id
                )
            )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

def get_leads_for_export():
    conn = get_connection()
    leads = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT l.id_lead, l.fecha_creacion, l.archivado, l.origen, l.chat_id,
                       c.nombre, c.apellido, c.numero_identificacion, c.correo,
                       c.telefono, c.celular, c.whatsapp,
                       p.tipo, p.condicion, p.direccion, p.valor,
                       u.ciudad, u.zona, u.departamento, u.pais
                FROM leads l
                LEFT JOIN contactos c ON l.id_lead = c.id_lead
                LEFT JOIN propiedades p ON l.id_lead = p.id_lead
                LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
                ORDER BY l.fecha_creacion DESC
            """
            cursor.execute(query)
            leads = cursor.fetchall()
        finally:
            conn.close()
    
    return leads

# Función auxiliar para limpiar texto
def clean_for_config(text):
    if text is None:
        return ""
    # Reemplazar comillas simples con su escape correspondiente
    return text.replace("'", "\\'")

@main.route('/bot/config', methods=['GET', 'POST'])
@login_required
def bot_config():
    # Definir rutas dentro de la función
    PID_FILE = os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.pid')
    
    # Comprobar si el bot ya está corriendo (por el archivo PID o por procesos)
    bot_running = False
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Verificar si el proceso existe
            process_info = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], 
                                     capture_output=True, text=True)
            if str(pid) in process_info.stdout:
                bot_running = True
        except:
            pass
    
    # Si el bot está corriendo pero la BD dice que no, actualizar la BD
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            if bot_running:
                cursor.execute("UPDATE bot_config SET is_active = TRUE WHERE id = 1")
                conn.commit()
        except:
            pass
    
    # Método GET
    config = {}
    bot_status = False
    last_update = ''
    bot_logs = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuración
            cursor.execute("SELECT * FROM bot_config WHERE id = 1")
            config = cursor.fetchone()
            
            if config:
                bot_status = config['is_active']
                last_update = config['last_update'].strftime('%d/%m/%Y %H:%M:%S') if config['last_update'] else ''
            
            # Obtener logs
            cursor.execute("SELECT * FROM bot_logs ORDER BY timestamp DESC LIMIT 100")
            logs = cursor.fetchall()
            
            for log in logs:
                timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                bot_logs.append(f"[{timestamp}] [{log['level']}] {log['message']}")
                
        except Exception as e:
            flash(f'Error al cargar configuración: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('bot_config.html', config=config, bot_status=bot_status, 
                           last_update=last_update, bot_logs=bot_logs)

@main.route('/bot/start', methods=['POST'])
@login_required
def start_bot():
    # Utilizar sys.executable para obtener el intérprete actual (más confiable)
    ENV_PYTHON = sys.executable
    
    # Asegurarnos que las rutas sean absolutas y correctas
    BOT_SCRIPT = os.path.abspath(os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.py'))
    PID_FILE = os.path.abspath(os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.pid'))
    LOG_FILE = os.path.abspath(os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.log'))
    
    # Verificar que el archivo del bot realmente existe
    if not os.path.exists(BOT_SCRIPT):
        return jsonify({"success": False, "message": f"No se encuentra el archivo del bot en: {BOT_SCRIPT}"})
    
    conn = get_connection()
    success = False
    message = ""
    
    try:
        # Abrir el archivo de log antes de pasarlo a subprocess
        with open(LOG_FILE, 'w', encoding='utf-8') as log_file:
            log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando bot...\n")
            
            # Verificar si el bot ya está corriendo
            if os.path.exists(PID_FILE):
                with open(PID_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
                try:
                    # Verificar si el proceso existe
                    process_info = subprocess.run(["tasklist", "/FI", f"PID eq {old_pid}"], 
                                            capture_output=True, text=True)
                    if str(old_pid) in process_info.stdout:
                        return jsonify({"success": True, "message": f"El bot ya está en ejecución (PID: {old_pid})"})
                except:
                    pass  # Si hay error, asumimos que el proceso no existe
            
            # Ejecutar directamente con Python en lugar de usar botrunner.bat
            try:
                process = subprocess.Popen(
                    [ENV_PYTHON, BOT_SCRIPT],
                    stdout=log_file,
                    stderr=log_file,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                # Esperar un momento para ver si el proceso termina inmediatamente
                time.sleep(2)
                if process.poll() is not None:
                    return jsonify({"success": False, "message": f"Bot terminó con error {process.poll()}"})
                
                # Proceso iniciado correctamente
                success = True
                message = f"Bot iniciado correctamente (PID: {process.pid})"
                log_file.write(f"Bot iniciado con PID: {process.pid}\n")
                
            except Exception as e:
                return jsonify({"success": False, "message": f"Error al iniciar el proceso: {str(e)}"})
            
        # Actualizar estado en la base de datos
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE bot_config SET is_active = TRUE, last_update = NOW() WHERE id = 1")
                conn.commit()
                
                # Guardar log
                cursor.execute(
                    "INSERT INTO bot_logs (level, message) VALUES (%s, %s)",
                    ('INFO', 'Bot iniciado por ' + current_user.nombre_usuario)
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                message += f" (Advertencia: Error al actualizar BD: {str(e)})"
    
    except Exception as e:
        return jsonify({"success": False, "message": f"Error inesperado: {str(e)}"})
    
    finally:
        if conn:
            conn.close()
    
    return jsonify({"success": success, "message": message})

@main.route('/bot/stop', methods=['POST'])
@login_required
def stop_bot():
    # Definir rutas dentro de la función
    PID_FILE = os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.pid')
    LOG_FILE = os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.log')
    
    conn = get_connection()
    success = False
    message = ""
    
    if conn:
        try:
            # Leer el PID del archivo
            if os.path.exists(PID_FILE):
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                
                # Primero intentar obtener información del proceso para verificar que existe
                try:
                    # Verificar si el proceso existe antes de intentar matarlo
                    process_info = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], 
                                             capture_output=True, text=True)
                    
                    if str(pid) in process_info.stdout:
                        # El proceso existe, intentar matarlo
                        subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      check=False)  # No usar check=True para evitar excepciones
                        message = f"Bot detenido (PID: {pid})"
                        
                        # Registrar en el log del bot
                        with open(LOG_FILE, 'a') as log_file:
                            log_file.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Bot detenido por usuario\n")
                    else:
                        message = f"El proceso con PID {pid} ya no existe"
                except Exception as e:
                    message = f"Error al verificar el proceso: {str(e)}"
                
                # Eliminar archivo PID en cualquier caso
                os.remove(PID_FILE)
            else:
                message = "No se encontró el archivo PID del bot"
            
            cursor = conn.cursor()
            
            # Actualizar estado en la base de datos
            cursor.execute("UPDATE bot_config SET is_active = FALSE, last_update = NOW() WHERE id = 1")
            conn.commit()
            
            # Guardar log
            cursor.execute(
                "INSERT INTO bot_logs (level, message) VALUES (%s, %s)",
                ('INFO', 'Bot detenido por ' + current_user.nombre_usuario)
            )
            conn.commit()
            
            success = True
            
        except Exception as e:
            conn.rollback()
            message = f"Error al detener el bot: {str(e)}"
        finally:
            conn.close()
    
    return jsonify({"success": success, "message": message})

@main.route('/bot/test', methods=['POST'])
@login_required
def test_bot():
    conn = get_connection()
    success = False
    message = ""
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener token
            cursor.execute("SELECT bot_token FROM bot_config WHERE id = 1")
            config = cursor.fetchone()
            
            if not config or not config['bot_token']:
                return jsonify({"success": False, "message": "El token del bot no está configurado"})
            
            # Probar conexión con la API de Telegram
            response = requests.get(f"https://api.telegram.org/bot{config['bot_token']}/getMe")
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info['ok']:
                    bot_name = bot_info['result']['username']
                    success = True
                    message = f"Conexión exitosa con el bot @{bot_name}"
                    
                    # Guardar log
                    cursor.execute(
                        "INSERT INTO bot_logs (level, message) VALUES (%s, %s)",
                        ('INFO', f"Prueba de conexión exitosa: @{bot_name}")
                    )
                    conn.commit()
                else:
                    message = "Error en la respuesta de Telegram: " + bot_info.get('description', 'Desconocido')
            else:
                message = f"Error al conectar con Telegram. Código: {response.status_code}"
                
        except Exception as e:
            message = f"Error al probar conexión: {str(e)}"
        finally:
            conn.close()
    
    return jsonify({"success": success, "message": message})

@main.route('/bot/debug', methods=['GET'])
@login_required
def debug_bot():
    """Endpoint para obtener información de depuración del bot"""
    BOT_SCRIPT = os.path.abspath(os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.py'))
    PID_FILE = os.path.abspath(os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.pid'))
    LOG_FILE = os.path.abspath(os.path.join(current_app.root_path, '..', 'telegram_bot', 'bot.log'))
    
    debug_info = {
        "python_path": sys.executable,
        "bot_script_path": BOT_SCRIPT,
        "bot_script_exists": os.path.exists(BOT_SCRIPT),
        "pid_file_path": PID_FILE,
        "pid_file_exists": os.path.exists(PID_FILE),
        "log_file_path": LOG_FILE,
        "log_file_exists": os.path.exists(LOG_FILE),
        "working_directory": os.getcwd(),
        "bot_running": False
    }
    
    # Verificar si el bot está ejecutándose
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
                
            # En Windows, usar tasklist para verificar si el proceso existe
            process_info = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"], 
                capture_output=True, text=True
            )
            debug_info["bot_running"] = str(pid) in process_info.stdout
            debug_info["process_info"] = process_info.stdout
            debug_info["pid"] = pid
        except Exception as e:
            debug_info["error_checking_process"] = str(e)
    
    # Leer últimas líneas del log
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()[-20:]  # Últimas 20 líneas
                debug_info["log_content"] = "".join(log_lines)
        except Exception as e:
            debug_info["error_reading_log"] = str(e)
    
    return jsonify(debug_info)

# Rutas para el CRUD de leads
@main.route('/leads', methods=['GET'])
@login_required
def list_leads():
    """Vista para listar todos los leads"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    conn = get_connection()
    leads = []
    total = 0
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Contar total para paginación
        cursor.execute("SELECT COUNT(*) as total FROM leads")
        total = cursor.fetchone()['total']
        
        # Consulta principal con JOIN para obtener datos relacionados
        query = """
        SELECT l.id_lead, l.fecha_creacion, l.origen,
               c.nombre, c.apellido, c.celular, c.correo,
               p.tipo, p.valor, 
               u.ciudad
        FROM leads l
        LEFT JOIN contactos c ON l.id_lead = c.id_lead
        LEFT JOIN propiedades p ON l.id_lead = p.id_lead
        LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
        ORDER BY l.fecha_creacion DESC
        LIMIT %s OFFSET %s
        """
        
        offset = (page - 1) * per_page
        cursor.execute(query, (per_page, offset))
        leads = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error al cargar leads: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()
    
    # Calcular número total de páginas
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('leads/list.html', 
                          leads=leads, 
                          page=page, 
                          total_pages=total_pages)

@main.route('/leads/<int:lead_id>', methods=['GET'])
@login_required
def view_lead(lead_id):
    """Vista para ver detalles de un lead específico"""
    conn = get_connection()
    lead = None
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Consulta completa para obtener todos los datos del lead
        query = """
        SELECT 
            l.id_lead, l.fecha_creacion, l.origen, l.chat_id,
            c.id_contacto, c.nombre, c.apellido, c.numero_identificacion, c.correo, 
            c.telefono, c.celular, c.whatsapp,
            p.id_propiedad, p.tipo, p.condicion, p.direccion, p.valor,
            u.id_ubicacion, u.ciudad, u.zona, u.departamento, u.pais
        FROM leads l
        LEFT JOIN contactos c ON l.id_lead = c.id_lead
        LEFT JOIN propiedades p ON l.id_lead = p.id_lead
        LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
        WHERE l.id_lead = %s
        """
        
        cursor.execute(query, (lead_id,))
        lead = cursor.fetchone()
        
        if not lead:
            flash('Lead no encontrado', 'error')
            return redirect(url_for('main.list_leads'))
        
    except Exception as e:
        flash(f'Error al cargar datos del lead: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()
    
    return render_template('leads/view.html', lead=lead)

@main.route('/leads/new', methods=['GET', 'POST'])
@login_required
def create_lead():
    """Vista para crear un nuevo lead"""
    if request.method == 'POST':
        # Obtener datos del formulario
        form_data = {
            # Datos de ubicación
            'ciudad': request.form.get('ciudad', ''),
            'zona': request.form.get('zona', ''),
            'departamento': request.form.get('departamento', ''),
            'pais': request.form.get('pais', 'Colombia'),
            
            # Datos de propiedad
            'tipo_propiedad': request.form.get('tipo_propiedad', ''),
            'condicion': request.form.get('condicion', ''),
            'direccion': request.form.get('direccion', ''),
            'valor': request.form.get('valor', ''),
            
            # Datos de contacto
            'nombre': request.form.get('nombre', ''),
            'apellido': request.form.get('apellido', ''),
            'identificacion': request.form.get('identificacion', ''),
            'email': request.form.get('email', ''),
            'telefono': request.form.get('telefono', ''),
            'celular': request.form.get('celular', ''),
            'whatsapp': 'whatsapp' in request.form,
            
            # Datos de lead
            'origen': request.form.get('origen', 'Web'),
        }
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Iniciar transacción
            conn.start_transaction()
            
            # 1. Insertar ubicación
            cursor.execute("""
                INSERT INTO ubicaciones (ciudad, zona, departamento, pais)
                VALUES (%s, %s, %s, %s)
            """, (
                form_data['ciudad'],
                form_data['zona'],
                form_data['departamento'],
                form_data['pais']
            ))
            id_ubicacion = cursor.lastrowid
            
            # 2. Insertar lead básico
            cursor.execute("""
                INSERT INTO leads (origen, fecha_creacion, archivado) 
                VALUES (%s, NOW(), 0)
            """, (form_data['origen'],))
            lead_id = cursor.lastrowid
            
            # 3. Insertar contacto
            cursor.execute("""
                INSERT INTO contactos (
                    id_lead, nombre, apellido, numero_identificacion, 
                    correo, telefono, celular, whatsapp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                lead_id,
                form_data['nombre'],
                form_data['apellido'],
                form_data['identificacion'],
                form_data['email'],
                form_data['telefono'],
                form_data['celular'],
                form_data['whatsapp']
            ))
            
            # 4. Insertar propiedad
            cursor.execute("""
                INSERT INTO propiedades (
                    id_lead, id_ubicacion, tipo, condicion, direccion, valor
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                lead_id,
                id_ubicacion,
                form_data['tipo_propiedad'],
                form_data['condicion'],
                form_data['direccion'],
                form_data['valor']
            ))
            
            # Confirmar cambios
            conn.commit()
            
            flash('Lead creado exitosamente', 'success')
            return redirect(url_for('main.view_lead', lead_id=lead_id))
            
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f'Error al crear lead: {str(e)}', 'error')
        finally:
            if conn:
                conn.close()
    
    return render_template('leads/create.html')

@main.route('/leads/<int:lead_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lead(lead_id):
    """Vista para editar un lead existente"""
    conn = get_connection()
    lead = None
    
    # Obtener datos actuales del lead si es GET o hubo error en POST
    if request.method == 'GET' or (request.method == 'POST' and 'error' in session):
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT 
                l.id_lead, l.fecha_creacion, l.origen, l.chat_id,
                c.id_contacto, c.nombre, c.apellido, c.numero_identificacion, c.correo, 
                c.telefono, c.celular, c.whatsapp,
                p.id_propiedad, p.tipo, p.condicion, p.direccion, p.valor,
                u.id_ubicacion, u.ciudad, u.zona, u.departamento, u.pais
            FROM leads l
            LEFT JOIN contactos c ON l.id_lead = c.id_lead
            LEFT JOIN propiedades p ON l.id_lead = p.id_lead
            LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
            WHERE l.id_lead = %s
            """
            
            cursor.execute(query, (lead_id,))
            lead = cursor.fetchone()
            
            if not lead:
                flash('Lead no encontrado', 'error')
                return redirect(url_for('main.list_leads'))
                
        except Exception as e:
            flash(f'Error al cargar datos del lead: {str(e)}', 'error')
            return redirect(url_for('main.list_leads'))
        finally:
            if conn:
                conn.close()
    
    # Procesar formulario si es POST
    if request.method == 'POST' and 'error' not in session:
        form_data = {
            # Datos de ubicación
            'id_ubicacion': request.form.get('id_ubicacion'),
            'ciudad': request.form.get('ciudad', ''),
            'zona': request.form.get('zona', ''),
            'departamento': request.form.get('departamento', ''),
            'pais': request.form.get('pais', 'Colombia'),
            
            # Datos de propiedad
            'id_propiedad': request.form.get('id_propiedad'),
            'tipo_propiedad': request.form.get('tipo_propiedad', ''),
            'condicion': request.form.get('condicion', ''),
            'direccion': request.form.get('direccion', ''),
            'valor': request.form.get('valor', ''),
            
            # Datos de contacto
            'id_contacto': request.form.get('id_contacto'),
            'nombre': request.form.get('nombre', ''),
            'apellido': request.form.get('apellido', ''),
            'identificacion': request.form.get('identificacion', ''),
            'email': request.form.get('email', ''),
            'telefono': request.form.get('telefono', ''),
            'celular': request.form.get('celular', ''),
            'whatsapp': 'whatsapp' in request.form,
        }
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Iniciar transacción
            conn.start_transaction()
            
            # 1. Actualizar ubicación
            cursor.execute("""
                UPDATE ubicaciones
                SET ciudad = %s, zona = %s, departamento = %s, pais = %s
                WHERE id_ubicacion = %s
            """, (
                form_data['ciudad'],
                form_data['zona'],
                form_data['departamento'],
                form_data['pais'],
                form_data['id_ubicacion']
            ))
            
            # 2. Actualizar contacto
            cursor.execute("""
                UPDATE contactos
                SET nombre = %s, apellido = %s, numero_identificacion = %s,
                    correo = %s, telefono = %s, celular = %s, whatsapp = %s
                WHERE id_contacto = %s
            """, (
                form_data['nombre'],
                form_data['apellido'],
                form_data['identificacion'],
                form_data['email'],
                form_data['telefono'],
                form_data['celular'],
                form_data['whatsapp'],
                form_data['id_contacto']
            ))
            
            # 3. Actualizar propiedad
            cursor.execute("""
                UPDATE propiedades
                SET tipo = %s, condicion = %s, direccion = %s, valor = %s
                WHERE id_propiedad = %s
            """, (
                form_data['tipo_propiedad'],
                form_data['condicion'],
                form_data['direccion'],
                form_data['valor'],
                form_data['id_propiedad']
            ))
            
            # Confirmar cambios
            conn.commit()
            
            flash('Lead actualizado exitosamente', 'success')
            return redirect(url_for('main.view_lead', lead_id=lead_id))
            
        except Exception as e:
            if conn:
                conn.rollback()
            session['error'] = True
            flash(f'Error al actualizar lead: {str(e)}', 'error')
        finally:
            if conn:
                conn.close()
            if 'error' in session:
                session.pop('error')
    
    return render_template('leads/edit.html', lead=lead)

@main.route('/leads/<int:lead_id>/delete', methods=['POST'])
@login_required
def delete_lead(lead_id):
    """Vista para eliminar un lead"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Iniciar transacción
        conn.start_transaction()
        
        # Consultar IDs relacionados antes de eliminar
        cursor.execute("SELECT id_propiedad FROM propiedades WHERE id_lead = %s", (lead_id,))
        propiedad = cursor.fetchone()
        
        cursor.execute("SELECT id_contacto FROM contactos WHERE id_lead = %s", (lead_id,))
        contacto = cursor.fetchone()
        
        cursor.execute("SELECT id_ubicacion FROM propiedades WHERE id_lead = %s", (lead_id,))
        ubicacion = cursor.fetchone()
        
        # Eliminar registros en orden inverso (por las restricciones de clave foránea)
        if propiedad:
            cursor.execute("DELETE FROM propiedades WHERE id_lead = %s", (lead_id,))
        
        if contacto:
            cursor.execute("DELETE FROM contactos WHERE id_lead = %s", (lead_id,))
        
        # Eliminar el lead
        cursor.execute("DELETE FROM leads WHERE id_lead = %s", (lead_id,))
        
        # Eliminar ubicación (si no hay otras propiedades que la usen)
        if ubicacion:
            cursor.execute("SELECT COUNT(*) as count FROM propiedades WHERE id_ubicacion = %s", (ubicacion[0],))
            if cursor.fetchone()['count'] == 0:
                cursor.execute("DELETE FROM ubicaciones WHERE id_ubicacion = %s", (ubicacion[0],))
        
        # Confirmar cambios
        conn.commit()
        
        flash('Lead eliminado exitosamente', 'success')
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error al eliminar lead: {str(e)}', 'error')
    finally:
        if conn:
            conn.close()
    
    return redirect(url_for('main.list_leads'))

# Añadir estados de seguimiento para leads
@main.route('/leads/<int:lead_id>/status', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    status = request.form.get('status')
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Añadir campo 'estado' a tabla leads
        cursor.execute(
            "UPDATE leads SET estado = %s, fecha_actualizacion = NOW() WHERE id_lead = %s",
            (status, lead_id)
        )
        conn.commit()
        flash('Estado actualizado correctamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar estado: {str(e)}', 'error')
    finally:
        conn.close()
    return redirect(url_for('main.view_lead', lead_id=lead_id))

@main.route('/leads/search-form')
@login_required
def search_form():
    """Mostrar formulario de búsqueda avanzada"""
    return render_template('leads/search_form.html')

@main.route('/leads/search', methods=['GET'])
@login_required
def search_leads():
    # Parámetros de búsqueda básicos
    search_term = request.args.get('q', '')
    tipo = request.args.get('tipo', '')
    ciudad = request.args.get('ciudad', '')
    departamento = request.args.get('departamento', '')
    zona = request.args.get('zona', '')
    min_valor = request.args.get('min_valor', '')
    max_valor = request.args.get('max_valor', '')
    
    # Parámetros de filtrado avanzado
    origen = request.args.get('origen', '')
    condicion = request.args.get('condicion', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    estado = request.args.get('estado', '')
    whatsapp = request.args.get('whatsapp', '')
    archivado = request.args.get('archivado', '')
    
    # Construir consulta dinámica
    query = """
    SELECT l.id_lead, l.fecha_creacion, l.origen, l.archivado, l.estado,
           c.nombre, c.apellido, c.celular, c.correo, c.whatsapp,
           p.tipo, p.valor, p.condicion, p.direccion,
           u.ciudad, u.departamento, u.zona
    FROM leads l
    LEFT JOIN contactos c ON l.id_lead = c.id_lead
    LEFT JOIN propiedades p ON l.id_lead = p.id_lead
    LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
    WHERE 1=1
    """
    params = []
    
    # Filtros básicos
    if search_term:
        query += " AND (c.nombre LIKE %s OR c.apellido LIKE %s OR c.celular LIKE %s OR c.correo LIKE %s OR p.direccion LIKE %s)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term])
    
    if tipo:
        query += " AND p.tipo = %s"
        params.append(tipo)
    
    if ciudad:
        query += " AND u.ciudad LIKE %s"
        params.append(f"%{ciudad}%")
    
    if departamento:
        query += " AND u.departamento LIKE %s"
        params.append(f"%{departamento}%")
        
    if zona:
        query += " AND u.zona LIKE %s"
        params.append(f"%{zona}%")
    
    if min_valor:
        query += " AND CAST(REPLACE(REPLACE(p.valor, '.', ''), ',', '') AS UNSIGNED) >= %s"
        params.append(min_valor.replace('.', '').replace(',', ''))
    
    if max_valor:
        query += " AND CAST(REPLACE(REPLACE(p.valor, '.', ''), ',', '') AS UNSIGNED) <= %s"
        params.append(max_valor.replace('.', '').replace(',', ''))
    
    # Filtros avanzados
    if origen:
        query += " AND l.origen = %s"
        params.append(origen)
    
    if condicion:
        query += " AND p.condicion = %s"
        params.append(condicion)
    
    if fecha_desde:
        query += " AND DATE(l.fecha_creacion) >= %s"
        params.append(fecha_desde)
    
    if fecha_hasta:
        query += " AND DATE(l.fecha_creacion) <= %s"
        params.append(fecha_hasta)
    
    if estado:
        query += " AND l.estado = %s"
        params.append(estado)
    
    if whatsapp == 'si':
        query += " AND c.whatsapp = 1"
    elif whatsapp == 'no':
        query += " AND c.whatsapp = 0"
    
    if archivado == 'si':
        query += " AND l.archivado = 1"
    elif archivado == 'no':
        query += " AND l.archivado = 0"
    
    query += " ORDER BY l.fecha_creacion DESC"
    
    # Ejecutar consulta
    conn = get_connection()
    leads = []
    total_results = 0
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        leads = cursor.fetchall()
        total_results = len(leads)
        
        # Formatear valores para mostrar
        for lead in leads:
            if lead['valor']:
                try:
                    valor_num = int(lead['valor'].replace('.', '').replace(',', ''))
                    lead['valor_formatted'] = f"${valor_num:,}".replace(',', '.')
                except:
                    lead['valor_formatted'] = lead['valor']
            else:
                lead['valor_formatted'] = 'No especificado'
                
    except Exception as e:
        flash(f'Error en la búsqueda: {str(e)}', 'error')
    finally:
        conn.close()
    
    return render_template(
        'leads/search_results.html', 
        leads=leads, 
        total_results=total_results,
        search_term=search_term,
        filters={
            'tipo': tipo,
            'ciudad': ciudad,
            'departamento': departamento,
            'zona': zona,
            'min_valor': min_valor,
            'max_valor': max_valor,
            'origen': origen,
            'condicion': condicion,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'estado': estado,
            'whatsapp': whatsapp,
            'archivado': archivado
        }
    )

@main.route('/notifications')
@login_required
def view_notifications():
    conn = get_connection()
    notificaciones = []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM notificaciones 
            WHERE id_usuario = %s 
            ORDER BY fecha_creacion DESC
        """, (current_user.id_usuario,))
        notificaciones = cursor.fetchall()
    except Exception as e:
        flash(f'Error al cargar notificaciones: {str(e)}', 'error')
    finally:
        conn.close()
    
    return render_template('notifications.html', notificaciones=notificaciones)

@main.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Marcar una notificación como leída"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notificaciones SET leida = TRUE WHERE id_notificacion = %s AND id_usuario = %s",
            (notif_id, current_user.id_usuario)
        )
        conn.commit()
        flash('Notificación marcada como leída', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('main.view_notifications'))

def crear_notificacion(id_usuario, mensaje):
    """Función para crear notificaciones en el sistema"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notificaciones (id_usuario, mensaje) VALUES (%s, %s)",
            (id_usuario, mensaje)
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error al crear notificación: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Añadir campo id_asesor a la tabla leads
@main.route('/leads/<int:lead_id>/assign', methods=['POST'])
@login_required
def assign_lead(lead_id):
    asesor_id = request.form.get('asesor_id')
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Asignar lead al asesor
        cursor.execute(
            "UPDATE leads SET id_asesor = %s, fecha_asignacion = NOW() WHERE id_lead = %s",
            (asesor_id, lead_id)
        )
        conn.commit()
        
        # Crear notificación para el asesor
        crear_notificacion(
            asesor_id, 
            f"Se te ha asignado un nuevo lead (ID: {lead_id}). Contáctalo lo antes posible."
        )
        
        flash('Lead asignado correctamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al asignar lead: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('main.view_lead', lead_id=lead_id))

@main.route('/my-leads')
@login_required
def my_leads():
    """Mostrar leads asignados al asesor actual"""
    conn = get_connection()
    leads = []
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT l.id_lead, l.fecha_creacion, l.origen,
                   c.nombre, c.apellido, c.celular, c.correo,
                   p.tipo, p.valor, 
                   u.ciudad
            FROM leads l
            LEFT JOIN contactos c ON l.id_lead = c.id_lead
            LEFT JOIN propiedades p ON l.id_lead = p.id_lead
            LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
            WHERE l.id_asesor = %s
            ORDER BY l.fecha_creacion DESC
        """, (current_user.id_usuario,))
        leads = cursor.fetchall()
    except Exception as e:
        flash(f'Error al cargar leads: {str(e)}', 'error')
    finally:
        conn.close()
    
    return render_template('leads/my_leads.html', leads=leads)

@main.route('/leads/<int:lead_id>/send-whatsapp', methods=['POST'])
@login_required
def send_whatsapp(lead_id):
    mensaje = request.form.get('mensaje')
    
    # Obtener número de contacto
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.celular, c.nombre, c.apellido
            FROM contactos c
            WHERE c.id_lead = %s
        """, (lead_id,))
        contacto = cursor.fetchone()
        
        if not contacto or not contacto['celular']:
            flash('No se encontró número de celular para este lead', 'error')
            return redirect(url_for('main.view_lead', lead_id=lead_id))
        
        # Formatear número (eliminar espacios y asegurar formato internacional)
        numero = contacto['celular'].replace(' ', '')
        if not numero.startswith('+'):
            numero = '+57' + numero  # Asumiendo Colombia
        
        # Integración con WhatsApp Business API (ejemplo con Twilio)
        try:
            from twilio.rest import Client
            
            # Credenciales de Twilio
            account_sid = 'TU_ACCOUNT_SID'
            auth_token = 'TU_AUTH_TOKEN'
            whatsapp_number = 'TU_NUMERO_WHATSAPP'
            
            client = Client(account_sid, auth_token)
            
            # Enviar mensaje
            message = client.messages.create(
                body=mensaje,
                from_=f'whatsapp:{whatsapp_number}',
                to=f'whatsapp:{numero}'
            )
            
            # Registrar envío en la base de datos
            cursor.execute("""
                INSERT INTO mensajes (id_lead, tipo, contenido, estado, fecha_envio)
                VALUES (%s, 'whatsapp', %s, 'enviado', NOW())
            """, (lead_id, mensaje))
            conn.commit()
            
            flash('Mensaje de WhatsApp enviado correctamente', 'success')
        except Exception as e:
            flash(f'Error al enviar mensaje: {str(e)}', 'error')
            
    except Exception as e:
        flash(f'Error al obtener datos del contacto: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('main.view_lead', lead_id=lead_id))

@main.route('/admin/backup-database', methods=['POST'])
@login_required
def backup_database():
    # Verificar si el usuario es administrador
    if not current_user.is_admin:
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Crear directorio para backups si no existe
        backup_dir = os.path.join(current_app.root_path, '..', 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Nombre del archivo de respaldo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'bogoker_backup_{timestamp}.sql')
        
        # Ejecutar comando mysqldump
        import subprocess
        
        # Obtener configuración de la BD (adaptar según tu configuración)
        db_config = {
            "host": "localhost",
            "database": "bogoker",
            "user": "root",
            "password": ""
        }
        
        command = [
            'mysqldump',
            f'--host={db_config["host"]}',
            f'--user={db_config["user"]}',
            f'--password={db_config["password"]}',
            db_config["database"],
            f'--result-file={backup_file}'
        ]
        
        process = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        
        if process.returncode != 0:
            raise Exception(f"Error en mysqldump: {process.stderr}")
        
        flash(f'Respaldo creado exitosamente: {os.path.basename(backup_file)}', 'success')
    except Exception as e:
        flash(f'Error al crear respaldo: {str(e)}', 'error')
    
    return redirect(url_for('main.dashboard'))