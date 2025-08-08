#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug específico para verificar qué datos está cargando
el formulario de edición de leads.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_connection import get_connection

def debug_edit_lead(lead_id=None):
    """Debug específico para el formulario de edición"""
    conn = get_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Si no se especifica un lead_id, usar el más reciente del bot
        if lead_id is None:
            cursor.execute("""
                SELECT id_lead FROM leads 
                WHERE origen = 'Telegram Bot' 
                ORDER BY fecha_creacion DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                lead_id = result['id_lead']
            else:
                print("No se encontraron leads del bot de Telegram")
                return
        
        print(f"=== DEBUG FORMULARIO DE EDICIÓN - LEAD ID: {lead_id} ===")
        
        # Esta es la MISMA consulta que usa la función edit_lead en routes.py
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
            print(f"❌ Lead {lead_id} no encontrado")
            return
        
        print(f"✅ Lead encontrado. Datos que se cargan en el formulario de edición:")
        print()
        
        # Información básica del lead
        print("📋 INFORMACIÓN BÁSICA:")
        print(f"  ID Lead: {lead['id_lead']}")
        print(f"  Origen: {lead['origen']}")
        print(f"  Fecha: {lead['fecha_creacion']}")
        print(f"  Chat ID: {lead['chat_id']}")
        print()
        
        # Datos de contacto
        print("👤 DATOS DE CONTACTO:")
        print(f"  ID Contacto: {lead['id_contacto']}")
        print(f"  Nombre: {lead['nombre']}")
        print(f"  Apellido: {lead['apellido']}")
        print(f"  Identificación: {lead['numero_identificacion']}")
        print(f"  Email: {lead['correo']}")
        print(f"  Teléfono: {lead['telefono']}")
        print(f"  Celular: {lead['celular']}")
        print(f"  WhatsApp: {lead['whatsapp']}")
        print()
        
        # Datos de ubicación
        print("📍 DATOS DE UBICACIÓN:")
        print(f"  ID Ubicación: {lead['id_ubicacion']}")
        print(f"  Ciudad: {lead['ciudad']}")
        print(f"  Zona: {lead['zona']}")
        print(f"  Departamento: {lead['departamento']}")
        print(f"  País: {lead['pais']}")
        print()
        
        # Datos de propiedad
        print("🏠 DATOS DE PROPIEDAD:")
        print(f"  ID Propiedad: {lead['id_propiedad']}")
        print(f"  Tipo: {lead['tipo']}")
        print(f"  Condición: '{lead['condicion']}'")
        print(f"  Dirección: {lead['direccion']}")
        print(f"  Valor: {lead['valor']} (tipo: {type(lead['valor'])})")
        print()
        
        # Verificar si hay campos None/vacíos
        print("⚠️  CAMPOS VACÍOS O NULOS:")
        campos_vacios = []
        for key, value in lead.items():
            if value is None or value == '':
                campos_vacios.append(f"  {key}: {value}")
        
        if campos_vacios:
            print("\n".join(campos_vacios))
        else:
            print("  ✅ Todos los campos tienen valores")
        
        print()
        print("=" * 60)
        
        # Comparar con lo que debería mostrar el template
        print("🎨 CÓMO SE VERÍAN ESTOS DATOS EN EL TEMPLATE:")
        print(f"  Nombre completo: {lead['nombre']} {lead['apellido']}")
        print(f"  Ubicación: {lead['ciudad']}, {lead['zona']}, {lead['departamento']}")
        print(f"  Propiedad: {lead['tipo']} en condición '{lead['condicion']}'")
        print(f"  Valor formateado: ${lead['valor']:,.0f} COP" if lead['valor'] else "Valor no disponible")
        
    except Exception as e:
        print(f"Error durante el debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    # Permitir especificar un lead_id como argumento
    import sys
    if len(sys.argv) > 1:
        try:
            lead_id = int(sys.argv[1])
            debug_edit_lead(lead_id)
        except ValueError:
            print("Error: El lead_id debe ser un número entero")
    else:
        debug_edit_lead()  # Usar el más reciente del bot
