# -*- coding: utf-8 -*-
"""
==============================================================================
YOUTUBE & TAISLY UPLOADER (Rotador Automático de Cuentas - VERSIÓN SHORTS)
==============================================================================
Maneja la conexión con la API de YouTube y la API privada de Taisly.
Aplica rotación matemática: Si publica en YT 0, va a Taisly Grupo 0.
"""

import os
import logging
import requests
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURACIÓN DE YOUTUBE
# ==============================================================================
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
MAX_ACCOUNTS = 3  # Ferumishop: ~3 cuentas de YouTube (token_0..token_2)
BASE_DIR = os.getcwd()

LOCKS_DIR = os.path.join(BASE_DIR, "locks_history_shorts")
if not os.path.exists(LOCKS_DIR):
    os.makedirs(LOCKS_DIR, exist_ok=True)

# ==============================================================================
# CONFIGURACIÓN DE TAISLY (API PRIVADA)
# ==============================================================================
TAISLY_API_KEY = os.getenv(
    "TAISLY_API_KEY",
    "taisly_dc97bfef8a1e9ae497d86440d8185f4d42f5f5ce138f1251c6e26654880566a8",
)
TAISLY_BASE_URL = "https://app.taisly.com/api/private"

# Mismo video, mismo grupo: YouTube N -> TikTok N + Instagram N + Facebook N
TAISLY_GROUPS = [
    # Grupo 0 / Cuenta 1: YT token_0 + TikTok ferumishop1 + IG ferumishop1 + FB Ferumishop
    [
        "6aa83b092011524ebf444c75",  # TikTok ferumishop1
        "6aa840742011524ebf444e6b",  # Instagram ferumishop1
        "6a45e119c66678771be37f48",  # Facebook Ferumishop
    ],
    # Grupo 1 / Cuenta 2: YT token_1 + TikTok ferumishop2 + IG ferumishop2 + FB Ferumi Shop Paraguay
    [
        "6aa83bf02011524ebf444cbf",  # TikTok ferumishop2
        "6aa840b92011524ebf444e82",  # Instagram ferumishop2
        "6aa83da72011524ebf444d94",  # Facebook Ferumi Shop Paraguay
    ],
    # Grupo 2 / Cuenta 3: YT token_2 + TikTok ferumishop3 + IG ferumishop3 + FB Ferumi Shop
    [
        "6aa83cf02011524ebf444d0e",  # TikTok ferumishop3
        "6aa8411a2011524ebf444f4a",  # Instagram ferumishop3
        "6aa83db22011524ebf444da2",  # Facebook Ferumi Shop
    ],
]

# ==============================================================================
# FUNCIONES DE ROTACIÓN Y ESTADO
# ==============================================================================
def get_next_account_index():
    rotator_file = os.path.join(LOCKS_DIR, "account_rotator.txt")
    current_index = 0
    
    if os.path.exists(rotator_file):
        try:
            with open(rotator_file, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    current_index = int(content)
        except Exception as e:
            logger.warning(f"  [YouTube/Taisly] Error leyendo rotación: {e}")
            
    next_index = (current_index + 1) % MAX_ACCOUNTS
    
    try:
        with open(rotator_file, 'w') as f:
            f.write(str(next_index))
    except Exception as e:
        logger.warning(f"  [YouTube/Taisly] No se pudo guardar rotación: {e}")
        
    logger.info(f"  [YouTube/Taisly] Toca usar Cuenta {next_index}")
    return next_index

def is_already_processed(article_id):
    if not article_id or article_id == "NO_ID":
        return False
    return os.path.exists(os.path.join(LOCKS_DIR, f"{article_id}.done"))

def mark_as_processed(article_id, video_id):
    if not article_id or article_id == "NO_ID":
        return
    try:
        done_file = os.path.join(LOCKS_DIR, f"{article_id}.done")
        with open(done_file, 'w') as f:
            f.write(f"Processed as SHORT at {datetime.now()} - YouTube ID: {video_id}")
    except Exception as e:
        logger.warning(f"  [YouTube/Taisly] No se pudo guardar historial para {article_id}: {e}")

# ==============================================================================
# INTEGRACIÓN TAISLY (TIKTOK + INSTAGRAM + FACEBOOK)
# ==============================================================================
def push_to_taisly(file_path, title, description, tags, account_index):
    """
    Publica el MISMO video en TikTok, Instagram y Facebook vía Taisly.
    Si YouTube usa la cuenta N, Taisly usa el grupo N (TikTok N + IG N + FB N).
    """
    # Mapeo matemático: YT 0->Grupo 0, YT 1->Grupo 1, YT 2->Grupo 2 (y vuelve a 0)
    grupo_taisly_index = account_index % len(TAISLY_GROUPS)
    plataformas_destino = TAISLY_GROUPS[grupo_taisly_index]
    
    logger.info(f"  [Taisly] Publicando en Grupo {grupo_taisly_index} (TikTok + Instagram + Facebook: {plataformas_destino})...")
    
    # Preparación para TikTok, Instagram Reels y Facebook Reels
    texto_post = f"{title}\n\n{description[:800]}..."

    if tags:
        texto_post += "\n\n" + " ".join([f"#{t}" for t in tags[:10]])

    headers = {
        'Authorization': f'Bearer {TAISLY_API_KEY}'
    }
    
    # En Taisly, el parámetro 'platforms' espera un string de un array (ej: '["id1", "id2"]')
    # json.dumps asegura las comillas dobles perfectas que la API necesita
    data = {
        'platforms': json.dumps(plataformas_destino),
        'description': texto_post
    }

    try:
        with open(file_path, 'rb') as video_file:
            files = {
                'video': (os.path.basename(file_path), video_file, 'video/mp4')
            }
            
            url_post = f"{TAISLY_BASE_URL}/post"
            response = requests.post(url_post, headers=headers, files=files, data=data, timeout=180)
            
            if response.status_code in [200, 201]:
                res_json = response.json()
                if res_json.get("success"):
                    logger.info(f"  [Taisly] ¡ÉXITO! Video publicado en TikTok, Instagram y Facebook (Grupo {grupo_taisly_index}).")
                    return True
                else:
                    logger.error(f"  [Taisly] Fallo lógico en Taisly: {res_json}")
                    return False
            else:
                logger.error(f"  [Taisly] Error HTTP {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"  [Taisly] Excepción de conexión: {e}")
        return False

# ==============================================================================
# AUTENTICACIÓN Y SUBIDA YOUTUBE
# ==============================================================================
def get_authenticated_service(account_index):
    creds = None
    token_file = os.path.join(BASE_DIR, f'token_{account_index}.json')
    
    if not os.path.exists(token_file):
        logger.warning(f"  [YouTube] Falta token: {token_file}")
        return None
        
    try:
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    except Exception as e:
        logger.error(f"  [YouTube] Token {account_index} corrupto: {e}")
        return None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.error(f"  [YouTube] Error refrescando token {account_index}: {e}")
                return None
        else:
            logger.error(f"  [YouTube] El token {account_index} requiere re-autorización.")
            return None
            
    try:
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"  [YouTube] Error construyendo servicio: {e}")
        return None

def upload_video(file_path, title, description, tags, category_id="26", thumbnail_path=None):
    if not os.path.exists(file_path):
        logger.error("  [YouTube] Archivo de video vertical no encontrado.")
        return None

    start_index = get_next_account_index()
    
    for i in range(MAX_ACCOUNTS):
        account_index = (start_index + i) % MAX_ACCOUNTS
        logger.info(f"  [YouTube] Intentando subida con la Cuenta {account_index}...")
        
        youtube = get_authenticated_service(account_index)
        if not youtube:
            continue
            
        body = {
            'snippet': {
                'title': title[:99],
                'description': description[:4900],
                'tags': tags[:15], 
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        try:
            media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)
            request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            
            response = None
            logger.info("  [YouTube] Transfiriendo bytes a YouTube Shorts...")
            
            while response is None:
                status, response = request.next_chunk()
                
            video_id = response.get('id')
            logger.info(f"  [YouTube] ¡ÉXITO! Short publicado: https://youtube.com/shorts/{video_id}")
            
            # ==========================================
            # EMPUJE INMEDIATO A TAISLY
            # ==========================================
            push_to_taisly(file_path, title, description, tags, account_index)
            
            # ==========================================
            # MINIATURA YOUTUBE (OPCIONAL)
            # ==========================================
            if not thumbnail_path:
                posible_jpg = file_path.rsplit('.', 1)[0] + '.jpg'
                if os.path.exists(posible_jpg):
                    thumbnail_path = posible_jpg

            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    logger.info("  [YouTube] Subiendo miniatura vertical...")
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    logger.info("  [YouTube] ¡Miniatura aplicada!")
                except Exception as e:
                    logger.warning(f"  [YouTube] Falló miniatura: {e}")

            return video_id
            
        except HttpError as e:
            if e.resp.status in [403, 429] and "quotaExceeded" in e.content.decode('utf-8'):
                logger.warning(f"  [YouTube] CUOTA LLENA en Cuenta {account_index}. Cambiando de canal...")
                continue 
            else:
                logger.error(f"  [YouTube] Error HTTP: {e}")
                break 
                
        except Exception as e:
            logger.error(f"  [YouTube] Error inesperado: {e}")
            break

    logger.error("  [YouTube] FALLO CRÍTICO: Todas las cuentas fallaron o sin cuota.")
    return None