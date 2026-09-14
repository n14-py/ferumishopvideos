# -*- coding: utf-8 -*-
"""
Configuración maestra del motor de Shorts Ferumishop.
Formato vertical 1080x1920 @ 30fps. Sin plantillas de noticias.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# 1. RUTAS
# ==============================================================================
BASE_DIR = os.getcwd()

TEMP_AUDIO_DIR = os.path.join(BASE_DIR, "temp_audio")
TEMP_VIDEO_DIR = os.path.join(BASE_DIR, "temp_video")
TEMP_IMG_DIR = os.path.join(BASE_DIR, "temp_processing")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

ASSETS_DIR = os.path.join(BASE_DIR, "assets_video")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
BRANDING_DIR = os.path.join(ASSETS_DIR, "branding")
BGM_DIR = os.path.join(ASSETS_DIR, "bgm")
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")
TRANSITIONS_DIR = os.path.join(SFX_DIR, "transiciones")

_font_candidates = [
    os.path.join(FONTS_DIR, "ARIBLK.TTF"),
    os.path.join(FONTS_DIR, "ARIALBD.TTF"),
    os.path.join(BASE_DIR, "arial.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_PATH = next((p for p in _font_candidates if os.path.exists(p)), "arial.ttf")

LOGO_PATH = os.path.join(BRANDING_DIR, "ferumi_logo.png")
LOGO_FALLBACK_PATH = os.path.join(BRANDING_DIR, "ferumi_logo_raw.png")

# ==============================================================================
# 2. RENDER 9:16 ALTA CALIDAD
# ==============================================================================
RESOLUTION_W = 1080
RESOLUTION_H = 1920
FPS = 30
VIDEO_PRESET = "veryfast"
VIDEO_CRF = 19
AUDIO_BITRATE = "192k"
AUDIO_RATE = 48000
TRANSITION_DURATION = 0.38

# ==============================================================================
# 3. OVERLAYS (logo centro un poco abajo, texto arriba, WhatsApp bajo el logo)
# ==============================================================================
LOGO_WIDTH = 520
LOGO_OPACITY = 0.68
LOGO_Y_OFFSET = 36

TOP_TEXT_Y = 155
TOP_TEXT_SIZE = 64
TOP_TEXT_MAX_CHARS = 20
TOP_TEXT_MAX_LINES = 3
TOP_TEXT_COLOR = "white"

WHATSAPP_FONT_SIZE = 42
WHATSAPP_COLOR = "white"
DEFAULT_WHATSAPP = os.getenv("FERUMI_WHATSAPP", "595987301591")

BRAND_NAME = "Ferumishop"

# ==============================================================================
# 4. VOCES TTS
# ==============================================================================
VOICES = {
    "mujer_1": "es-MX-DaliaNeural",
    "mujer_2": "es-ES-ElviraNeural",
    "hombre_1": "es-AR-TomasNeural",
    "hombre_2": "es-MX-JorgeNeural",
}

DEFAULT_VOICE = "mujer_1"

# Transiciones xfade virales (FFmpeg 6+)
XFADE_TRANSITIONS = [
    "fadeblack",
    "wipeleft",
    "wiperight",
    "slideleft",
    "slideright",
    "circlecrop",
    "smoothleft",
]

# ==============================================================================
# 5. CARPETAS
# ==============================================================================
def init_directories():
    directories = [
        TEMP_AUDIO_DIR, TEMP_VIDEO_DIR, TEMP_IMG_DIR, OUTPUT_DIR,
        ASSETS_DIR, FONTS_DIR, BRANDING_DIR, BGM_DIR, SFX_DIR, TRANSITIONS_DIR,
        os.path.join(BGM_DIR, "shop"),
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

init_directories()
