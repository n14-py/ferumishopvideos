# -*- coding: utf-8 -*-
"""
==============================================================================
SCENE BUILDER (El Constructor de Escenas - VERSIÓN SHORTS)
==============================================================================
Toma recursos y crea comandos de FFmpeg complejos.
Contiene la magia de adaptar imágenes horizontales a formato vertical 9:16
utilizando fondos desenfocados (blur).
"""

import os
import textwrap
import logging
from config import *
from ffmpeg_core import execute_ffmpeg_command

logger = logging.getLogger(__name__)

# ==============================================================================
# FORMATEO DE TEXTO MULTILÍNEA
# ==============================================================================
def wrap_text_for_ffmpeg(text, max_chars):
    """
    Inserta saltos de línea (\n) para que el texto encaje en pantalla.
    Adaptado a las columnas más estrechas del formato Short.
    """
    if not text:
        return ""
    wrapper = textwrap.TextWrapper(width=max_chars)
    word_list = wrapper.wrap(text=text)
    # En Shorts, podemos permitir hasta 4 líneas cortas sin saturar
    if len(word_list) > 4:
        return "\\n".join(word_list[:4]) + "..."
    return "\\n".join(word_list)

# ==============================================================================
# CONSTRUCTOR DE INTROS (VERSIÓN SHORT)
# ==============================================================================
def build_intro_scene(template_path, audio_path, bgm_path, title_text, output_path):
    """
    Construye la intro. Asume que tu intro de Canva ya es 1080x1920.
    """
    logger.info("  [Scene Builder] Construyendo Escena Intro (Short)...")
    
    filename = os.path.basename(template_path)
    config = get_layout_config(filename)
    
    clean_title = wrap_text_for_ffmpeg(title_text, config["max_letras_por_linea"])
    
    x = config["texto_x"]
    y = config["texto_y"]
    color = config["color"]
    size = config["font_size"]
    shadow = "shadowcolor=black@0.8:shadowx=0:shadowy=0"
    
    audio_filter = ""
    audio_map = "-map 1:a"
    
    if bgm_path:
        audio_filter = f"[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=2:weights=1 0.1[aout];"
        audio_map = "-map [aout]"

    # Escalamos a 1080x1920 por seguridad por si alguna intro no es de ese tamaño exacto
    filter_complex = (
        f"[0:v]scale={RESOLUTION_W}:{RESOLUTION_H}[v_scaled];"
        f"[v_scaled]drawtext=fontfile='{FONT_PATH}':text='{clean_title}':"
        f"fontcolor={color}:fontsize={size}:{shadow}:x={x}:y={y}[vout];"
        f"{audio_filter}"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", template_path, 
        "-i", audio_path     
    ]
    
    if bgm_path:
        cmd.extend(["-i", bgm_path]) 
        
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[vout]", 
        *audio_map.split(),
        "-c:v", "libx264", "-preset", VIDEO_PRESET, "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
    ])
    
    return execute_ffmpeg_command(cmd)

# ==============================================================================
# CONSTRUCTOR DE CUERPO DE NOTICIA (MAGIA VERTICAL + CHROMA KEY)
# ==============================================================================
def build_body_scene(image_path, template_path, audio_path, bgm_path, sfx_path, overlay_text, output_path):
    """
    El corazón del Short.
    Toma una imagen, crea un fondo borroso 1080x1920, le pone la imagen nítida al medio,
    y encima perfora tu video verde del presentador.
    """
    logger.info("  [Scene Builder] Construyendo Escena de Cuerpo (Magia Vertical + Chroma)...")
    
    filename = os.path.basename(template_path)
    config = get_layout_config(filename)
    clean_text = wrap_text_for_ffmpeg(overlay_text, config["max_letras_por_linea"])
    
    x = config["texto_x"]
    y = config["texto_y"]
    color = config["color"]
    size = config["font_size"]
    shadow = "shadowcolor=black@0.8:shadowx=0:shadowy=0"
    
    # --- LA PIPELINE VISUAL DE SHORTS ---
    # [bg_blur]: Expande la imagen y la desenfoca para llenar 1080x1920
    # [img_sharp]: Escala la imagen original a 1080 de ancho (mantiene el alto proporcional)
    # [bg_combined]: Superpone la nítida sobre la desenfocada justo en el centro
    # [v_scaled]: Fuerza tu video verde (template) a ser exactamente 1080x1920
    # [v_keyed]: Perfora el verde del video
    # [comp]: Pega al presentador sobre el fondo combinado
    # [vout]: Dibuja los textos encima
    
    filter_complex = (
        f"[0:v]scale={RESOLUTION_W}:{RESOLUTION_H}:force_original_aspect_ratio=increase,"
        f"crop={RESOLUTION_W}:{RESOLUTION_H}:(iw-ow)/2:(ih-oh)/2,boxblur=20:5[bg_blur];"
        f"[0:v]scale={RESOLUTION_W}:-1[img_sharp];"
        f"[bg_blur][img_sharp]overlay=0:(H-h)/2[bg_combined];"
        f"[1:v]scale={RESOLUTION_W}:{RESOLUTION_H}[v_scaled];"
        f"[v_scaled]chromakey={CHROMA_COLOR}:{CHROMA_SIMILARITY}:{CHROMA_BLEND}[v_keyed];"
        f"[bg_combined][v_keyed]overlay=0:0:shortest=1[comp];"
        f"[comp]drawtext=fontfile='{FONT_PATH}':text='{clean_text}':"
        f"fontcolor={color}:fontsize={size}:{shadow}:x={x}:y={y}[vout];"
    )
    
    # Mezclador Dinámico de Audio (Igual de robusto que en tu V2.0)
    audio_inputs = "[2:a]"
    input_count = 1
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "60", "-i", image_path, # [0:v] Imagen real 
        "-stream_loop", "-1", "-i", template_path,  # [1:v] Video Verde en bucle
        "-i", audio_path                            # [2:a] Voz TTS
    ]
    
    if bgm_path:
        cmd.extend(["-i", bgm_path])                # [3:a]
        audio_inputs += "[3:a]"
        input_count += 1
        
    if sfx_path:
        cmd.extend(["-i", sfx_path])                # [4:a]
        audio_inputs += "[4:a]"
        input_count += 1

    if input_count > 1:
        filter_complex += f"{audio_inputs}amix=inputs={input_count}:duration=first:dropout_transition=2:weights=1 0.1 0.3[aout]"
        audio_map = "-map [aout]"
    else:
        filter_complex = filter_complex.rstrip(';')
        audio_map = "-map 2:a"
        
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[vout]", 
        *audio_map.split(),
        "-c:v", "libx264", "-preset", VIDEO_PRESET, "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
    ])
    
    return execute_ffmpeg_command(cmd)