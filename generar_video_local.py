# -*- coding: utf-8 -*-
"""
Genera el Short en TU PC. No sube a YouTube ni a Taisly.

Cómo usarlo (elegí UNA forma):

  1) Copiá json_prueba_salida.json a esta carpeta y corré:
       python generar_video_local.py

  2) Pasá la ruta:
       python generar_video_local.py C:\\ruta\\json_prueba_salida.json

  3) Pegá el JSON entero entre las comillas de PEGAR_JSON (abajo) y corré:
       python generar_video_local.py

El video queda en la carpeta output/
"""

import json
import logging
import os
import sys

# --- Opción 3: pegá acá el JSON de ferumishop (si lo dejás vacío, lee el archivo) ---
PEGAR_JSON = r"""
"""

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

from main_orchestrator import process_video_payload
from config import OUTPUT_DIR


def cargar_payload():
    pegado = PEGAR_JSON.strip()
    if pegado:
        print("  Leyendo JSON pegado en PEGAR_JSON...")
        return json.loads(pegado)

    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "json_prueba_salida.json")
    if not os.path.isfile(ruta):
        print(f"No encontré el JSON: {ruta}")
        print("Copiá json_prueba_salida.json acá, pasá la ruta, o pegaló en PEGAR_JSON.")
        sys.exit(1)

    print(f"  Leyendo {ruta}...")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def main():
    payload = cargar_payload()
    if not isinstance(payload, dict) or not payload.get("scenes"):
        print("El JSON no trae 'scenes'. Revisá json_prueba_salida.json")
        sys.exit(1)

    n = len(payload.get("scenes") or [])
    print(f"  Escenas: {n}")
    print(f"  ID: {payload.get('article_id') or payload.get('product_id')}")
    print(f"  WhatsApp: {payload.get('whatsapp')}")
    print("  Fabricando Short vertical (sin subir a redes)...\n")

    video = process_video_payload(payload)
    if not video or not os.path.exists(video):
        print("Falló la generación. Mirá el log de arriba.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  LISTO  (solo local, no se subió nada)")
    print(f"  Video: {os.path.abspath(video)}")
    print(f"  Carpeta: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
