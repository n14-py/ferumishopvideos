# -*- coding: utf-8 -*-
"""
==============================================================================
CONFIGURACIÓN MAESTRA DEL SISTEMA DE VIDEO (VERSIÓN SHORTS 9:16)
==============================================================================
Centraliza rutas, configuraciones de FFmpeg, coordenadas de overlays y voces.
Adaptado estrictamente para formato vertical 1080x1920.
"""

import os
from dotenv import load_dotenv

# Cargar las variables del archivo .env automáticamente
load_dotenv()

# ==============================================================================
# 1. RUTAS DE DIRECTORIOS
# ==============================================================================
BASE_DIR = os.getcwd()

TEMP_AUDIO_DIR = os.path.join(BASE_DIR, "temp_audio")
TEMP_VIDEO_DIR = os.path.join(BASE_DIR, "temp_video")
TEMP_IMG_DIR = os.path.join(BASE_DIR, "temp_processing")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

ASSETS_DIR = os.path.join(BASE_DIR, "assets_video")

# --- TRUCO MAESTRO PARA FFMPEG EN WINDOWS ---
# Generamos la ruta absoluta y escapamos los dos puntos de la unidad C:
_raw_font = os.path.join(ASSETS_DIR, "fonts", "fuente.ttf")
FONT_PATH = "arial.ttf"

TEMPLATES_DIR = os.path.join(ASSETS_DIR, "templates")
BGM_DIR = os.path.join(ASSETS_DIR, "bgm")
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")

# ==============================================================================
# 2. CONFIGURACIÓN DE PANTALLA Y RENDERIZADO (FORMATO SHORT)
# ==============================================================================
RESOLUTION_W = 1080
RESOLUTION_H = 1920
FPS = 24
VIDEO_PRESET = "ultrafast"
CHROMA_COLOR = "0x00FF00"
CHROMA_SIMILARITY = "0.30"
CHROMA_BLEND = "0.10"

# ==============================================================================
# 3. VOCES DEL TTS (Edge TTS)
# ==============================================================================
VOICES = {
    "mujer_1": "es-MX-DaliaNeural",
    "mujer_2": "es-ES-ElviraNeural",
    "hombre_1": "es-AR-TomasNeural",
    "hombre_2": "es-CO-TomasNeural"
}

# ==============================================================================
# 4. DICCIONARIO DE COORDENADAS PARA 20 LAYOUTS EXACTOS (1080x1920)
# ==============================================================================
# Adaptado para que los textos caigan en la misma proporción visual (tercio inferior)

DEFAULT_LAYOUT = {
    "texto_x": 50, 
    "texto_y": 1500, 
    "color": "white", 
    "font_size": 55, 
    "max_letras_por_linea": 35
}

LAYOUT_CONFIG = {
    # --- INTROS ---
    "intro_layout_01.mp4": {"texto_x": -1000, "texto_y": -1500, "color": "white", "font_size": 85, "max_letras_por_linea": 18},
    "intro_layout_02.mp4": {"texto_x": -1000, "texto_y": -1500, "color": "yellow", "font_size": 70, "max_letras_por_linea": 25},
    "intro_layout_03.mp4": {"texto_x": -1000, "texto_y": -1500, "color": "white", "font_size": 75, "max_letras_por_linea": 18},
    "intro_layout_04.mp4": {"texto_x": -1000, "texto_y": -1500, "color": "red", "font_size": 80, "max_letras_por_linea": 45},
    "intro_layout_05.mp4": {"texto_x": -1000, "texto_y": -1500, "color": "white", "font_size": 65, "max_letras_por_linea": 30},

    # --- HOMBRE ---
    "hombre_layout_01.mp4": {"texto_x": 102,  "texto_y": 1560, "color": "white", "font_size": 38, "max_letras_por_linea": 45},
    "hombre_layout_02.mp4": {"texto_x": 102, "texto_y": 1421, "color": "white", "font_size": 42, "max_letras_por_linea": 40},
    "hombre_layout_03.mp4": {"texto_x": 102,  "texto_y": 1574, "color": "yellow", "font_size": 42, "max_letras_por_linea": 45},
    "hombre_layout_04.mp4": {"texto_x": 99, "texto_y": 1364, "color": "white", "font_size": 38, "max_letras_por_linea": 45},
    "hombre_layout_05.mp4": {"texto_x": 44,  "texto_y": 1661, "color": "white", "font_size": 39, "max_letras_por_linea": 45},
    "hombre_layout_06.mp4": {"texto_x": 85,  "texto_y": 1352, "color": "white", "font_size": 39, "max_letras_por_linea": 45},
    "hombre_layout_07.mp4": {"texto_x": 65,  "texto_y": 1565, "color": "white", "font_size": 39, "max_letras_por_linea": 45},

    # --- MUJER ---
    "mujer_layout_01.mp4": {"texto_x": 102,  "texto_y": 1560, "color": "white", "font_size": 38, "max_letras_por_linea": 45},
    "mujer_layout_02.mp4": {"texto_x": 102, "texto_y": 1421, "color": "white", "font_size": 42, "max_letras_por_linea": 40},
    "mujer_layout_03.mp4": {"texto_x": 102,  "texto_y": 1574, "color": "yellow", "font_size": 42, "max_letras_por_linea":45},
    "mujer_layout_04.mp4": {"texto_x": 99, "texto_y": 1364, "color": "white", "font_size": 38, "max_letras_por_linea": 45},
    "mujer_layout_05.mp4": {"texto_x": 44,  "texto_y": 1661, "color": "white", "font_size": 39, "max_letras_por_linea": 45},
    "mujer_layout_06.mp4": {"texto_x": 85,  "texto_y": 1352, "color": "white", "font_size": 39, "max_letras_por_linea": 45},
    "mujer_layout_07.mp4": {"texto_x": 65,  "texto_y": 1565, "color": "white", "font_size": 39, "max_letras_por_linea": 45},

    # --- GRÁFICOS (SIN PRESENTADOR) ---
    "grafico_layout_01.mp4": {"texto_x": 102,  "texto_y": 1560, "color": "white", "font_size": 38, "max_letras_por_linea": 45},
    "grafico_layout_02.mp4": {"texto_x": 102, "texto_y": 1421, "color": "white", "font_size": 42, "max_letras_por_linea": 40},
    "grafico_layout_03.mp4": {"texto_x": 102,  "texto_y": 1574, "color": "yellow", "font_size": 42, "max_letras_por_linea": 45},
    "grafico_layout_04.mp4": {"texto_x": 99, "texto_y": 1364, "color": "white", "font_size": 38, "max_letras_por_linea": 45},
    "grafico_layout_05.mp4": {"texto_x": 44,  "texto_y": 1661, "color": "white", "font_size": 39, "max_letras_por_linea": 45},
    "grafico_layout_06.mp4": {"texto_x": 78,  "texto_y": 1352, "color": "white", "font_size": 39, "max_letras_por_linea": 45},
    "grafico_layout_07.mp4": {"texto_x": 65,  "texto_y": 1565, "color": "white", "font_size": 39, "max_letras_por_linea": 45},
}

def get_layout_config(filename):
    return LAYOUT_CONFIG.get(filename, DEFAULT_LAYOUT)

# ==============================================================================
# 5. CREACIÓN AUTOMÁTICA DE CARPETAS
# ==============================================================================
def init_directories():
    directories = [
        TEMP_AUDIO_DIR, TEMP_VIDEO_DIR, TEMP_IMG_DIR, OUTPUT_DIR,
        ASSETS_DIR, 
        os.path.join(ASSETS_DIR, "fonts"),
        TEMPLATES_DIR, BGM_DIR, SFX_DIR,
        os.path.join(TEMPLATES_DIR, "intros"),
        os.path.join(TEMPLATES_DIR, "hombre"),
        os.path.join(TEMPLATES_DIR, "mujer"),
        os.path.join(TEMPLATES_DIR, "sin_presentador"),
        os.path.join(BGM_DIR, "urgencia"),
        os.path.join(BGM_DIR, "analisis"),
        os.path.join(BGM_DIR, "tension"),
        os.path.join(SFX_DIR, "transiciones"),
        os.path.join(SFX_DIR, "impactos"),
        os.path.join(SFX_DIR, "alertas"),
        os.path.join(SFX_DIR, "tecnologia")
    ]
    for directory in directories:
        # Solo creamos la carpeta si no es un string con la ruta "engañada" de FFmpeg
        if "C\:" not in directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

init_directories()