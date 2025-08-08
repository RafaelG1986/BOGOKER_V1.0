#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug específico para probar el filtro avanzado de leads.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_connection import get_connection

def test_search_query():
    """Probar la consulta de búsqueda avanzada con diferentes parámetros"""
    
    print("=== DEBUG FILTRO AVANZADO DE LEADS ===")
    
    # Parámetros de prueba
    test_params = {
        'search_term': '',
        'tipo': 'Casa',
        'ciudad': 'Bogota',
        'departamento': '',
        'zona': '',
        'min_valor': '',
        'max_valor': '',
        'origen': 'Telegram Bot',
        'condicion': 'Usada - Excelente estado',
        'fecha_desde': '',
        'fecha_hasta': '',
        'estado': '',
        'whatsapp': '',
        'archivado': 'no'
    }
    
    print("Parámetros de prueba:")
    for key, value in test_params.items():
        if value:
            print(f"  {key}: '{value}'")
    print()
    
    # Construir consulta (igual que en routes.py corregido)
    query = """
    SELECT l.id_lead, l.fecha_creacion, l.origen, l.archivado,
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
    
    # Aplicar filtros
    search_term = test_params['search_term']
    if search_term:
        query += " AND (c.nombre LIKE %s OR c.apellido LIKE %s OR c.celular LIKE %s OR c.correo LIKE %s OR p.direccion LIKE %s)"
        term = f"%{search_term}%"
        params.extend([term, term, term, term, term])
    
    tipo = test_params['tipo']
    if tipo:
        query += " AND p.tipo = %s"
        params.append(tipo)
    
    ciudad = test_params['ciudad']
    if ciudad:
        query += " AND u.ciudad LIKE %s"
        params.append(f"%{ciudad}%")
    
    departamento = test_params['departamento']
    if departamento:
        query += " AND u.departamento LIKE %s"
        params.append(f"%{departamento}%")
        
    zona = test_params['zona']
    if zona:
        query += " AND u.zona LIKE %s"
        params.append(f"%{zona}%")
    
    min_valor = test_params['min_valor']
    if min_valor:
        query += " AND CAST(REPLACE(REPLACE(p.valor, '.', ''), ',', '') AS UNSIGNED) >= %s"
        params.append(min_valor.replace('.', '').replace(',', ''))
    
    max_valor = test_params['max_valor']
    if max_valor:
        query += " AND CAST(REPLACE(REPLACE(p.valor, '.', ''), ',', '') AS UNSIGNED) <= %s"
        params.append(max_valor.replace('.', '').replace(',', ''))
    
    # Filtros avanzados
    origen = test_params['origen']
    if origen:
        query += " AND l.origen = %s"
        params.append(origen)
    
    condicion = test_params['condicion']
    if condicion:
        query += " AND p.condicion = %s"
        params.append(condicion)
    
    fecha_desde = test_params['fecha_desde']
    if fecha_desde:
        query += " AND DATE(l.fecha_creacion) >= %s"
        params.append(fecha_desde)
    
    fecha_hasta = test_params['fecha_hasta']
    if fecha_hasta:
        query += " AND DATE(l.fecha_creacion) <= %s"
        params.append(fecha_hasta)
    
    # Campo 'estado' removido porque no existe en la tabla leads
    
    whatsapp = test_params['whatsapp']
    if whatsapp == 'si':
        query += " AND c.whatsapp = 1"
    elif whatsapp == 'no':
        query += " AND c.whatsapp = 0"
    
    archivado = test_params['archivado']
    if archivado == 'si':
        query += " AND l.archivado = 1"
    elif archivado == 'no':
        query += " AND l.archivado = 0"
    
    query += " ORDER BY l.fecha_creacion DESC"
    
    print("CONSULTA SQL GENERADA:")
    print(query)
    print()
    print("PARÁMETROS:")
    print(params)
    print()
    
    # Ejecutar consulta
    conn = get_connection()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        leads = cursor.fetchall()
        
        print(f"✅ RESULTADOS ENCONTRADOS: {len(leads)}")
        print()
        
        if leads:
            print("LEADS ENCONTRADOS:")
            for i, lead in enumerate(leads, 1):
                print(f"  {i}. Lead #{lead['id_lead']}")
                print(f"     Cliente: {lead['nombre']} {lead['apellido']}")
                print(f"     Tipo: {lead['tipo']}")
                print(f"     Condición: {lead['condicion']}")
                print(f"     Ciudad: {lead['ciudad']}")
                print(f"     Origen: {lead['origen']}")
                print(f"     Fecha: {lead['fecha_creacion']}")
                print(f"     Archivado: {'Sí' if lead['archivado'] else 'No'}")
                print()
        else:
            print("❌ No se encontraron resultados con los filtros aplicados")
            
            # Probar consulta más simple para debug
            print("\n=== PROBANDO CONSULTA SIMPLE ===")
            simple_query = "SELECT COUNT(*) as total FROM leads WHERE 1=1"
            if archivado == 'no':
                simple_query += " AND archivado = 0"
            
            cursor.execute(simple_query)
            total = cursor.fetchone()['total']
            print(f"Total de leads en la BD (no archivados): {total}")
            
            # Probar por tipo
            if tipo:
                type_query = "SELECT COUNT(*) as total FROM propiedades WHERE tipo = %s"
                cursor.execute(type_query, (tipo,))
                total_tipo = cursor.fetchone()['total']
                print(f"Total de propiedades tipo '{tipo}': {total_tipo}")
            
            # Probar por ciudad
            if ciudad:
                city_query = "SELECT COUNT(*) as total FROM ubicaciones WHERE ciudad LIKE %s"
                cursor.execute(city_query, (f"%{ciudad}%",))
                total_ciudad = cursor.fetchone()['total']
                print(f"Total de ubicaciones con ciudad '{ciudad}': {total_ciudad}")
                
    except Exception as e:
        print(f"❌ Error ejecutando la consulta: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def test_simple_search():
    """Probar búsqueda simple sin filtros"""
    print("\n=== PRUEBA DE BÚSQUEDA SIMPLE (SIN FILTROS) ===")
    
    query = """
    SELECT l.id_lead, l.fecha_creacion, l.origen, l.archivado,
           c.nombre, c.apellido, c.celular, c.correo, c.whatsapp,
           p.tipo, p.valor, p.condicion, p.direccion,
           u.ciudad, u.departamento, u.zona
    FROM leads l
    LEFT JOIN contactos c ON l.id_lead = c.id_lead
    LEFT JOIN propiedades p ON l.id_lead = p.id_lead
    LEFT JOIN ubicaciones u ON p.id_ubicacion = u.id_ubicacion
    WHERE l.archivado = 0
    ORDER BY l.fecha_creacion DESC
    LIMIT 5
    """
    
    conn = get_connection()
    if not conn:
        print("❌ Error: No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        leads = cursor.fetchall()
        
        print(f"✅ ÚLTIMOS 5 LEADS (NO ARCHIVADOS): {len(leads)}")
        
        for i, lead in enumerate(leads, 1):
            print(f"  {i}. Lead #{lead['id_lead']} - {lead['nombre']} {lead['apellido']}")
            print(f"     Tipo: {lead['tipo']} | Condición: {lead['condicion']}")
            print(f"     Ciudad: {lead['ciudad']} | Origen: {lead['origen']}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_search_query()
    test_simple_search()
