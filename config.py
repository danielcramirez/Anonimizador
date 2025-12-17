import os

# Rutas basicas y secreto de sesion para Flask
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
SECRET_KEY = "anonimizador-gpl"

# Token por defecto para reemplazo en texto
MASK_TOKEN = "[REDACTADO]"

# Limites suaves para PDFs grandes; evita cargar todo en memoria.
MAX_PAGES_TO_SCAN = None  # None = todas; asignar entero para cortar lectura
HIT_MAX_PER_PAGE = 0      # 0 = sin limite en search_for

# Opciones de OCR
OCR_ENABLED_DEFAULT = False  # se puede activar en la UI
OCR_LANGUAGE = "spa"

ALLOWED_EXTENSIONS = {"pdf"}

# Crear carpetas necesarias
for path in (UPLOADS_DIR, OUTPUTS_DIR):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass
