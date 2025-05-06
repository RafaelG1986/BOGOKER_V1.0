import pytest

# Pruebas simuladas para el módulo de leads
def test_lead_creation():
    # Simulación de creación de un lead
    lead = {
        "nombre": "Juan", 
        "apellido": "Pérez",
        "telefono": "3101234567",
        "propiedad": "Apartamento"
    }
    assert "nombre" in lead
    assert lead["nombre"] == "Juan"

def test_lead_validation():
    # Probar validación de datos de lead
    lead = {"nombre": "", "telefono": "123"}
    errors = validate_lead(lead)
    assert len(errors) > 0
    assert "El nombre es obligatorio" in errors

def validate_lead(lead):
    errors = []
    if not lead.get("nombre"):
        errors.append("El nombre es obligatorio")
    if len(lead.get("telefono", "")) < 7:
        errors.append("El teléfono debe tener al menos 7 dígitos")
    return errors