#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la estructura real de las tablas de la base de datos.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_connection import get_connection

def show_table_structure():
    """Mostrar la estructura de todas las tablas relevantes"""
    conn = get_connection()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        tables = ['leads', 'contactos', 'propiedades', 'ubicaciones']
        
        for table in tables:
            print(f"=== ESTRUCTURA DE LA TABLA: {table.upper()} ===")
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            
            for col in columns:
                print(f"  {col['Field']:<20} | {col['Type']:<15} | NULL: {col['Null']:<3} | Default: {col['Default']}")
            print()
        
        # Verificar datos de ejemplo
        print("=== DATOS DE EJEMPLO ===")
        cursor.execute("""
            SELECT l.*, c.nombre, c.apellido, p.tipo, p.condicion, u.ciudad
            FROM leads l
            LEFT JOIN contactos c ON l.id_lead = c.id_lead
            LEFT JOIN propiedades p ON l.id_lead = p.id_lead
            LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
            LIMIT 3
        """)
        
        leads = cursor.fetchall()
        for lead in leads:
            print(f"Lead #{lead['id_lead']}:")
            for key, value in lead.items():
                print(f"  {key}: {value}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    show_table_structure()
