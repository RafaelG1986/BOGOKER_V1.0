#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug para verificar cómo se están almacenando y recuperando los valores
de propiedades desde la base de datos.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_connection import get_connection

def debug_valores():
    """Verifica los valores en la base de datos"""
    conn = get_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener algunos leads recientes con sus valores y condiciones
        query = """
        SELECT 
            l.id_lead,
            l.origen,
            l.fecha_creacion,
            p.valor,
            p.tipo,
            p.condicion,
            c.nombre,
            c.apellido
        FROM leads l
        LEFT JOIN propiedades p ON l.id_lead = p.id_lead
        LEFT JOIN contactos c ON l.id_lead = c.id_lead
        WHERE p.valor IS NOT NULL
        ORDER BY l.fecha_creacion DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print("=== DEBUG DE VALORES EN BASE DE DATOS ===")
        print(f"Total de registros encontrados: {len(results)}")
        print()
        
        for i, row in enumerate(results, 1):
            print(f"Lead #{i}:")
            print(f"  ID: {row['id_lead']}")
            print(f"  Origen: {row['origen']}")
            print(f"  Cliente: {row['nombre']} {row['apellido']}")
            print(f"  Tipo: {row['tipo']}")
            print(f"  Condición: '{row['condicion']}'")
            print(f"  Valor RAW: '{row['valor']}'")
            print(f"  Tipo de dato: {type(row['valor'])}")
            print(f"  Longitud: {len(str(row['valor'])) if row['valor'] else 0}")
            
            # Intentar convertir a número
            try:
                if row['valor']:
                    valor_str = str(row['valor'])
                    # Intentar como entero
                    valor_int = int(float(valor_str))
                    print(f"  Como entero: {valor_int:,}")
                    print(f"  Formateado: ${valor_int:,}".replace(',', '.'))
                else:
                    print(f"  Valor es None o vacío")
            except Exception as e:
                print(f"  Error al convertir: {e}")
            
            print("-" * 40)
        
        # Verificar también la estructura de la tabla
        print("\n=== ESTRUCTURA DE LA TABLA PROPIEDADES ===")
        cursor.execute("DESCRIBE propiedades")
        columns = cursor.fetchall()
        
        for col in columns:
            if col['Field'] == 'valor':
                print(f"Campo 'valor':")
                print(f"  Tipo: {col['Type']}")
                print(f"  Null: {col['Null']}")
                print(f"  Default: {col['Default']}")
                print(f"  Extra: {col['Extra']}")
        
    except Exception as e:
        print(f"Error durante la consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_valores()
