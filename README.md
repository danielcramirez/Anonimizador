# PDF Anonimizador (Flask + CLI)

Herramienta para extraer texto de PDFs, detectar datos personales (PII) y generar una version anonimizada siguiendo la guia del Archivo General de la Nacion.

## Proposito
- Interfaz web simple (Flask) para subir, analizar y anonimizar PDFs.
- Procesamiento local con spaCy + regex y redacciones en el PDF (PyMuPDF).
- OCR opcional con Tesseract/pytesseract para PDFs escaneados.

## Stack
- **Web**: Flask, Jinja2, Bootstrap (CDN).
- **PDF**: pdfplumber (texto embebido) + PyMuPDF (redaction).
- **NLP**: spaCy (es_core_news_md) + regex.
- **OCR opcional**: Tesseract + pytesseract (Apache 2.0).

## Uso web
1) Activa el entorno: `venv\Scripts\activate`
2) Instala dependencias: `pip install -r requirements.txt`
3) Ejecuta: `python app.py` y abre `http://localhost:5000`

## Uso CLI
```
python app.py --input ruta\archivo.pdf --output uploads\anonimizados\salida.pdf --texto --ocr
```
- `--texto` guarda el texto anonimizado en .txt.
- `--ocr` intenta OCR si no hay texto embebido.
- `--mask` cambia el token de reemplazo (por defecto `[REDACTADO]`).

## Notas
- Patrones editables en `nlp/detector.py`.
- Token de reemplazo y rutas en `config.py`.
- Las redacciones se aplican con `add_redact_annot` + `apply_redactions` para eliminar el texto original del PDF.
