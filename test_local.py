# -*- coding: utf-8 -*-
"""
Prueba local del motor Ferumishop.
Genera un Short VERTICAL 1080x1920 @ 30fps con ~8 escenas de venta.
"""

import json
import os
import logging
import subprocess
from config import TEMP_VIDEO_DIR, OUTPUT_DIR, RESOLUTION_W, RESOLUTION_H, FPS
from main_orchestrator import process_video_payload

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

COLORES = [
    "0x3b0a24", "0x6a1b4d", "0xc2185b", "0xff69b4",
    "0x880e4f", "0xad1457", "0xd81b60", "0xf06292",
]


def _hacer_clip_prueba(path, color, label, segundos=3.2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s={RESOLUTION_W}x{RESOLUTION_H}:r={FPS}:d={segundos}",
        "-f", "lavfi", "-i", f"sine=frequency=220:sample_rate=48000:duration={segundos}",
        "-vf", f"drawtext=text='{label}':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=h*0.78:borderw=3",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
        path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return path


def payload_venta_8_escenas(clips):
    with open(os.path.join(os.path.dirname(__file__) or ".", "ejemplo_payload_venta.json"), encoding="utf-8") as f:
        payload = json.load(f)
    payload["article_id"] = "ferumi_venta_8escenas"
    for i, scene in enumerate(payload["scenes"]):
        scene["video_url"] = clips[i]
    return payload


def ejecutar_prueba_ferumi():
    print("\n" + "=" * 70)
    print(f"  SHORT VERTICAL Ferumishop  {RESOLUTION_W}x{RESOLUTION_H} @ {FPS}fps  |  8 escenas")
    print("=" * 70 + "\n")

    os.makedirs(TEMP_VIDEO_DIR, exist_ok=True)
    clips = []
    for i, color in enumerate(COLORES, start=1):
        path = os.path.join(TEMP_VIDEO_DIR, f"demo_producto_{i}.mp4")
        _hacer_clip_prueba(path, color, f"ESCENA {i}", 3.0)
        clips.append(path)

    payload = payload_venta_8_escenas(clips)
    resultado = process_video_payload(payload)

    print("\n" + "=" * 70)
    if resultado:
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
        print(f"  SHORT FERUMI OK (VERTICAL)\n  Archivo: {resultado}")
        print(probe.stdout)
        w = None
        h = None
        for line in probe.stdout.splitlines():
            if line.startswith("width="):
                w = int(line.split("=")[1])
            if line.startswith("height="):
                h = int(line.split("=")[1])
        if w != RESOLUTION_W or h != RESOLUTION_H:
            raise SystemExit(f"ERROR: se esperaba {RESOLUTION_W}x{RESOLUTION_H} vertical, salió {w}x{h}")
        if h <= w:
            raise SystemExit(f"ERROR: el video no es vertical (w={w} h={h})")
        print(f"  Confirmado VERTICAL 9:16: {w}x{h}  (NO es horizontal)")
    else:
        print("  LA PRUEBA FALLÓ. Revisá los logs.")
    print("=" * 70 + "\n")
    return resultado


if __name__ == "__main__":
    ejecutar_prueba_ferumi()
