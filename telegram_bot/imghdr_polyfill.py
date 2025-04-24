# -*- coding: utf-8 -*-

def what(file, h=None):
    """
    Función de reemplazo para imghdr.what que devuelve el tipo de imagen
    basado en su extensión o contenido.
    """
    if h is not None:
        # Verificar por magic numbers (primeros bytes del archivo)
        if h.startswith(b'\xff\xd8'):
            return 'jpeg'
        if h.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        if h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
            return 'gif'
        if h.startswith(b'BM'):
            return 'bmp'
        if h.startswith(b'RIFF') and h[8:12] == b'WEBP':
            return 'webp'
        return None
    
    # Si no tenemos datos de encabezado, verificar por extensión del archivo
    if isinstance(file, str):
        file = file.lower()
        if file.endswith('.jpg') or file.endswith('.jpeg'):
            return 'jpeg'
        if file.endswith('.png'):
            return 'png'
        if file.endswith('.gif'):
            return 'gif'
        if file.endswith('.bmp'):
            return 'bmp'
        if file.endswith('.webp'):
            return 'webp'
    
    return None