#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración para actualizar las condiciones antiguas del bot
a las nuevas condiciones consistentes con el CRUD.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_connection import get_connection

def migrar_condiciones():
    """Migra las condiciones antiguas a las nuevas"""
    
    # Mapeo de condiciones antiguas a nuevas
    mapeo_condiciones = {
        'Excelente': 'Usada - Excelente estado',
        'Buena': 'Usada - Buen estado', 
        'Regular': 'Usada - Necesita remodelación',
        'Necesita reparaciones': 'Usada - Necesita remodelación',
        'Venta': 'Nueva',  # Corregir esta condición extraña
        'Usado': 'Usada - Buen estado',  # Por si hay otras variantes
    }
    
    conn = get_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Primero, obtener todas las condiciones actuales
        print("=== ANÁLISIS DE CONDICIONES ACTUALES ===")
        cursor.execute("SELECT DISTINCT condicion, COUNT(*) as cantidad FROM propiedades GROUP BY condicion")
        condiciones_actuales = cursor.fetchall()
        
        print("Condiciones encontradas en la base de datos:")
        for row in condiciones_actuales:
            condicion = row['condicion']
            cantidad = row['cantidad']
            if condicion in mapeo_condiciones:
                print(f"  '{condicion}' ({cantidad} registros) -> SE MIGRARÁ A: '{mapeo_condiciones[condicion]}'")
            else:
                print(f"  '{condicion}' ({cantidad} registros) -> YA ES CORRECTA")
        
        print("\n¿Deseas proceder con la migración? (s/n): ", end="")
        respuesta = input().lower().strip()
        
        if respuesta != 's':
            print("Migración cancelada.")
            return
        
        # Proceder con la migración
        print("\n=== INICIANDO MIGRACIÓN ===")
        total_actualizados = 0
        
        for condicion_antigua, condicion_nueva in mapeo_condiciones.items():
            # Verificar cuántos registros tienen esta condición
            cursor.execute("SELECT COUNT(*) as count FROM propiedades WHERE condicion = %s", (condicion_antigua,))
            count_result = cursor.fetchone()
            count = count_result['count'] if count_result else 0
            
            if count > 0:
                print(f"Migrando {count} registros de '{condicion_antigua}' a '{condicion_nueva}'...")
                
                # Actualizar los registros
                cursor.execute("""
                    UPDATE propiedades 
                    SET condicion = %s 
                    WHERE condicion = %s
                """, (condicion_nueva, condicion_antigua))
                
                total_actualizados += count
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n✅ MIGRACIÓN COMPLETADA")
        print(f"Total de registros actualizados: {total_actualizados}")
        
        # Mostrar el estado final
        print("\n=== ESTADO FINAL ===")
        cursor.execute("SELECT DISTINCT condicion, COUNT(*) as cantidad FROM propiedades GROUP BY condicion ORDER BY condicion")
        condiciones_finales = cursor.fetchall()
        
        print("Condiciones después de la migración:")
        for row in condiciones_finales:
            print(f"  '{row['condicion']}': {row['cantidad']} registros")
            
    except Exception as e:
        print(f"Error durante la migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrar_condiciones()
