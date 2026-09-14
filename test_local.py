# -*- coding: utf-8 -*-
"""
Prueba local del motor Ferumishop.
Genera clips de prueba 9:16 y arma un Short con logo + texto + WhatsApp + whoosh.
"""

import os
import logging
import subprocess
from config import TEMP_VIDEO_DIR, OUTPUT_DIR, RESOLUTION_W, RESOLUTION_H, FPS
from main_orchestrator import process_video_payload

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")


def _hacer_clip_prueba(path, color, label, segundos=3.5):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s={RESOLUTION_W}x{RESOLUTION_H}:r={FPS}:d={segundos}",
        "-f", "lavfi", "-i", f"sine=frequency=220:sample_rate=48000:duration={segundos}",
        "-vf", f"drawtext=text='{label}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h*0.72:borderw=3",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
        path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return path


def ejecutar_prueba_ferumi():
    print("\n" + "=" * 70)
    print("  PRUEBA FERUMISHOP: video tras video + logo + texto + WhatsApp")
    print("=" * 70 + "\n")

    os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)
    clip_a = os.path.join(TEMP_VIDEO_DIR, "demo_producto_a.mp4")
    clip_b = os.path.join(TEMP_VIDEO_DIR, "demo_producto_b.mp4")
    clip_c = os.path.join(TEMP_VIDEO_DIR, "demo_producto_c.mp4")
    _hacer_clip_prueba(clip_a, "0x3b0a24", "CLIP 1 PRODUCTO", 3.2)
    _hacer_clip_prueba(clip_b, "0x6a1b4d", "CLIP 2 PRODUCTO", 3.2)
    _hacer_clip_prueba(clip_c, "0xc2185b", "CLIP 3 PRODUCTO", 3.2)

    payload = {
        "article_id": "ferumi_demo_local",
        "youtube_title": "Labial mate Ferumi que dura todo el día",
        "youtube_description": "Comprá en ferumi.shop 💖 Pedí por WhatsApp.\n\n#ferumi #maquillaje #shorts",
        "youtube_tags": ["ferumi", "ferumishop", "maquillaje", "labial", "shorts"],
        "whatsapp": "595987301591",
        "texto_pantalla": "Labial mate 💖",
        "scenes": [
            {
                "type": "video",
                "text": "Este labial mate de Ferumi te deja los labios perfectos todo el día, linda.",
                "texto_pantalla": "Labial mate que dura",
                "video_url": clip_a,
                "voice": "mujer_1",
            },
            {
                "type": "video",
                "text": "Colores intensos, textura suave y el brillo justo para salir ahora mismo.",
                "texto_pantalla": "Color intenso",
                "video_url": clip_b,
                "voice": "mujer_1",
            },
            {
                "type": "body",
                "text": "Pedilo por WhatsApp y te lo llevamos. Ferumi Shop, Paraguay.",
                "texto_pantalla": "Pedilo por WhatsApp",
                "video_url": clip_c,
                "voice": "mujer_1",
            },
        ],
    }

    resultado = process_video_payload(payload)
    print("\n" + "=" * 70)
    if resultado:
        print(f"  SHORT FERUMI OK\n  Archivo: {resultado}")
        probe = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate,codec_name",
                "-show_entries", "format=duration,size",
                "-of", "default=noprint_wrappers=1",
                resultado,
            ],
            capture_output=True, text=True,
        )
        print(probe.stdout)
    else:
        print("  LA PRUEBA FALLÓ. Revisá los logs.")
    print("=" * 70 + "\n")
    return resultado


if __name__ == "__main__":
    ejecutar_prueba_ferumi()
