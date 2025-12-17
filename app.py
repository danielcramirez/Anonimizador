"""
Aplicacion Flask + CLI para anonimizar PDFs.
Combina UI web (upload/analizar/anonimizar) y modo CLI.
"""

import argparse
import os
import sys
from typing import Dict, List

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

from config import (
    UPLOADS_DIR,
    OUTPUTS_DIR,
    SECRET_KEY,
    ALLOWED_EXTENSIONS,
    MASK_TOKEN,
    OCR_ENABLED_DEFAULT,
)
from pdf.extractor import extraer_texto
from nlp.pipeline import analizar_texto
from nlp.anonymizer import anonimizar_texto
from pdf.writer import anonimizar_pdf


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def asegurar_directorios():
    for path in (UPLOADS_DIR, OUTPUTS_DIR):
        try:
            os.makedirs(path, exist_ok=True)
        except OSError:
            pass


def listar_archivos(base_path: str) -> List[Dict[str, str]]:
    """Devuelve archivos en un directorio para mostrarlos en tablas."""
    if not os.path.exists(base_path):
        return []
    items = []
    for nombre in sorted(os.listdir(base_path)):
        ruta = os.path.join(base_path, nombre)
        if not os.path.isfile(ruta):
            continue
        info = os.stat(ruta)
        items.append(
            {
                "name": nombre,
                "size_kb": round(info.st_size / 1024, 1),
                "mtime": info.st_mtime,
            }
        )
    return items


def crear_app() -> Flask:
    asegurar_directorios()
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["UPLOAD_FOLDER"] = UPLOADS_DIR
    return app


app = crear_app()


@app.route("/", methods=["GET"])
def index():
    # Limpia estado previo para no precargar hallazgos antiguos
    session.clear()
    return render_template(
        "index.html",
        resultados=session.get("hallazgos"),
        texto=session.get("texto"),
        texto_anon=session.get("texto_anon"),
        pdf_salida=session.get("pdf_salida_name"),
        txt_salida=session.get("txt_salida_name"),
        usar_ocr=session.get("usar_ocr", OCR_ENABLED_DEFAULT),
    )


@app.route("/analizar", methods=["POST"])
def analizar():
    archivo = request.files.get("pdf")
    usar_ocr = bool(request.form.get("usar_ocr"))
    session.pop("texto_anon", None)
    session.pop("pdf_salida_name", None)
    session.pop("txt_salida_name", None)

    if not archivo or archivo.filename == "" or not allowed_file(archivo.filename):
        return render_template("index.html", error="Sube un PDF válido.", usar_ocr=usar_ocr)

    filename = secure_filename(archivo.filename)
    ruta_pdf = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    asegurar_directorios()
    archivo.save(ruta_pdf)

    try:
        texto = extraer_texto(ruta_pdf, usar_ocr=usar_ocr)
        if not texto:
            raise ValueError("No se pudo extraer texto; intenta activar OCR si no estaba activo.")

        hallazgos = analizar_texto(texto)

        session["pdf_nombre"] = filename
        session["pdf_path"] = ruta_pdf
        session["texto"] = texto
        session["hallazgos"] = hallazgos
        session["usar_ocr"] = usar_ocr

        return render_template(
            "index.html",
            resultados=hallazgos,
            texto=texto,
            usar_ocr=usar_ocr,
        )
    except Exception as exc:  # pragma: no cover - UI path
        return render_template("index.html", error=f"No se pudo procesar el PDF: {exc}", usar_ocr=usar_ocr)


@app.route("/anonimizar", methods=["POST"])
def anonimizar():
    texto = session.get("texto")
    hallazgos = session.get("hallazgos") or []
    pdf_nombre = session.get("pdf_nombre")
    pdf_path = session.get("pdf_path")

    if not texto or not pdf_nombre or not pdf_path:
        return redirect(url_for("index"))

    valores = sorted({h["value"] for h in hallazgos}, key=len, reverse=True)
    texto_anon = anonimizar_texto(texto, hallazgos, MASK_TOKEN)

    nombre_salida_pdf = f"anon_{pdf_nombre}"
    ruta_salida_pdf = os.path.join(OUTPUTS_DIR, nombre_salida_pdf)
    asegurar_directorios()
    anonimizar_pdf(pdf_path, ruta_salida_pdf, valores, token=MASK_TOKEN)

    nombre_salida_txt = f"{os.path.splitext(nombre_salida_pdf)[0]}.txt"
    ruta_salida_txt = os.path.join(OUTPUTS_DIR, nombre_salida_txt)
    with open(ruta_salida_txt, "w", encoding="utf-8") as f:
        f.write(texto_anon)

    session["texto_anon"] = texto_anon
    session["pdf_salida_name"] = nombre_salida_pdf
    session["txt_salida_name"] = nombre_salida_txt

    return render_template(
        "index.html",
        resultados=hallazgos,
        texto=session.get("texto"),
        texto_anon=texto_anon,
        pdf_salida=nombre_salida_pdf,
        txt_salida=nombre_salida_txt,
        usar_ocr=session.get("usar_ocr", OCR_ENABLED_DEFAULT),
        archivos_subidos=listar_archivos(UPLOADS_DIR),
        archivos_anonimizados=listar_archivos(OUTPUTS_DIR),
    )


@app.route("/descargar/<path:filename>", methods=["GET"])
def descargar(filename: str):
    destino = os.path.join(OUTPUTS_DIR, filename)
    if os.path.exists(destino):
        return send_from_directory(OUTPUTS_DIR, filename, as_attachment=True)
    destino_upload = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(destino_upload):
        return send_from_directory(UPLOADS_DIR, filename, as_attachment=True)
    return "Archivo no encontrado", 404


# ===========================
# Modo CLI
# ===========================
def procesar_cli(args) -> Dict[str, str]:
    asegurar_directorios()
    texto = extraer_texto(args.input, usar_ocr=args.ocr)
    if not texto:
        raise ValueError("No se pudo extraer texto; intente con --ocr si es escaneado.")

    hallazgos = analizar_texto(texto)
    valores = sorted({h["value"] for h in hallazgos}, key=len, reverse=True)

    salida_pdf = args.output or os.path.join(OUTPUTS_DIR, f"anon_{os.path.basename(args.input)}")
    salida_pdf = os.path.abspath(salida_pdf)
    anonimizar_pdf(args.input, salida_pdf, valores, token=args.mask)

    resultado = {"pdf_salida": salida_pdf}

    if args.texto:
        salida_txt = f"{os.path.splitext(salida_pdf)[0]}.txt"
        with open(salida_txt, "w", encoding="utf-8") as f:
            f.write(anonimizar_texto(texto, hallazgos, args.mask))
        resultado["texto_salida"] = salida_txt

    return resultado


def main():
    parser = argparse.ArgumentParser(description="Anonimizador de PDFs (CLI). Ejecuta sin argumentos para UI web.")
    parser.add_argument("--input", "-i", help="Ruta del PDF de entrada.")
    parser.add_argument("--output", "-o", help="Ruta del PDF anonimizado de salida.")
    parser.add_argument("--mask", "-m", default=MASK_TOKEN, help="Token de reemplazo.")
    parser.add_argument("--texto", action="store_true", help="Guardar tambien texto anonimo en .txt")
    parser.add_argument("--ocr", action="store_true", help="Usar OCR si no hay texto embebido.")

    if len(sys.argv) == 1:
        app.run(debug=True)
        return

    args = parser.parse_args()
    if not args.input:
        parser.error("Debe proporcionar --input para modo CLI.")

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"No se encontro el archivo: {args.input}")

    resultado = procesar_cli(args)
    print("PDF anonimizado generado:")
    print(f" - PDF: {resultado['pdf_salida']}")
    if "texto_salida" in resultado:
        print(f" - TXT: {resultado['texto_salida']}")


if __name__ == "__main__":
    main()
