# -*- coding: utf-8 -*-
# ==============================================================================
# TEST LOCAL (Simulador de Node.js + MongoDB) - EDICIÓN SHORTS MULTI-ANUNCIO
# ==============================================================================
# Este payload simula a Gemini inyectando los 3 tipos de anuncios de tu base de datos:
# 1. ad_mencion (Mención IA con presentador)
# 2. banner_flotante (Inyectado como ad_banner_url en una escena normal)
# 3. ad_video (Pausa comercial a pantalla completa)

import logging
from main_orchestrator import process_video_payload

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

def ejecutar_prueba_multianuncio():
    print("\n" + "="*70)
    print("  INICIANDO PRUEBA SHORTS: 1 NOTICIA + 3 TIPOS DE ANUNCIOS (9:16)")
    print("="*70 + "\n")

    # NOTA: Rellena las URLs con los links completos (las que me pasaste terminaban en "...")
    URL_MEDIA_PRUEBA = "https://pub-32bf4851ff77488ebe727d3dad5fbb4d.r2.dev/anuncios/ad_1786730829706_399759833.mp4"
    URL_MEDIA = "https://pub-32bf4851ff77488ebe727d3dad5fbb4d.r2.dev/anuncios/ad_1786732163471_656237920.jpeg"
    URL = "https://pub-32bf4851ff77488ebe727d3dad5fbb4d.r2.dev/anuncios/ad_1786734825986_647602327.jpeg"
    

    payload =  {
  "youtube_title": "¡Misterio Espacial! NASA detecta señal repetitiva",
  "youtube_description": "¡Suscríbete para más noticias!\n Lee la nota completa: https://www.noticias.lat/articulo/id_test_shorts\n\n#shorts #noticias\n\nLa comunidad astronómica internacional se encuentra conmocionada tras el último anuncio de la NASA. Astrónomos utilizando el telescopio espacial James Webb han detectado una misteriosa y potente señal de radio que se repite exactamente cada 16 días, proveniente de una galaxia ubicada a millones de años luz de la Tierra. A diferencia de otras ráfagas rápidas de radio descubiertas en el pasado, este nuevo fenómeno presenta un patrón matemático casi perfecto, lo que ha desatado todo tipo de teorías. Algunos científicos sugieren que podría tratarse de una estrella de neutrones altamente magnetizada, conocida como púlsar, que gira a velocidades vertiginosas. Sin embargo, una pequeña facción de investigadores no descarta que estemos ante un intento de comunicación de una civilización extraterres",
  "youtube_tags": [
    "nasa",
    "espacio",
    "jameswebb",
    "extraterrestres",
    "astronomia",
    "shorts"
  ],
  "scenes": [
    {
      "type": "intro",
      "text": "¡Misterio total en el cosmos! La NASA acaba de captar una señal de radio extremadamente extraña, potente y muy repetitiva en el espacio.",
      "layout_category": "sin_presentador",
      "voice": "hombre_1",
      "bgm_mood": "urgencia",
      "sfx_type": "impactos"
    },
    {
      "type": "body",
      "image_url": "https://img.freepik.com/fotos-premium/galaxia-espacio-estrellas_942223-110.jpg",
      "layout_category": "mujer",
      "text": "El telescopio espacial James Webb detectó una señal misteriosa proveniente de una galaxia lejana, ubicada a millones de años luz de nuestro planeta.",
      "voice": "mujer_1",
      "bgm_mood": "tension",
      "sfx_type": "transiciones"
    },
    {
      "type": "pexels",
      "termino_busqueda": "space signal",
      "ad_banner_url": "https://pub-32bf4851ff77488ebe727d3dad5fbb4d.r2.dev/anuncios/ad_1786751597341_210092002.jpeg",
      "layout_category": "sin_presentador",
      "text": "Lo más impactante es que la señal se repite exactamente cada dieciséis días, siguiendo un patrón matemático casi perfecto y sumamente preciso.",
      "voice": "hombre_1",
      "bgm_mood": "tension",
      "sfx_type": "tecnologia"
    },
    {
      "type": "body",
      "image_url": "https://img.freepik.com/fotos-premium/galaxia-espacio-estrellas_942223-110.jpg",
      "layout_category": "mujer",
      "text": "Este fenómeno ha desatado diversas teorías científicas, ya que no se parece a ninguna ráfaga de radio vista anteriormente en el cosmos.",
      "voice": "mujer_1",
      "bgm_mood": "analisis",
      "sfx_type": "transiciones"
    },
    {
      "type": "pexels",
      "termino_busqueda": "neutron star",
      "layout_category": "sin_presentador",
      "text": "Algunos expertos sugieren que podría ser un púlsar, que es básicamente una estrella de neutrones magnetizada que gira a velocidades realmente vertiginosas.",
      "voice": "hombre_1",
      "bgm_mood": "analisis",
      "sfx_type": "tecnologia"
    },
    {
      "type": "pexels",
      "termino_busqueda": "extraterrestrial signal",
      "ad_banner_url": "https://pub-32bf4851ff77488ebe727d3dad5fbb4d.r2.dev/anuncios/ad_1786751597341_210092002.jpeg",
      "layout_category": "mujer",
      "text": "Sin embargo, una facción de investigadores no descarta que estemos ante un posible intento de comunicación de una civilización extraterrestre muy avanzada.",
      "voice": "mujer_1",
      "bgm_mood": "tension",
      "sfx_type": "alertas"
    },
    {
      "type": "pexels",
      "termino_busqueda": "radio telescope",
      "layout_category": "sin_presentador",
      "text": "Las agencias de Europa, Japón y China ya apuntan sus radiotelescopios hacia las coordenadas exactas para descifrar este gran enigma intergaláctico.",
      "voice": "hombre_1",
      "bgm_mood": "analisis",
      "sfx_type": "transiciones"
    },
    {
      "type": "body",
      "image_url": "https://img.freepik.com/fotos-premium/galaxia-espacio-estrellas_942223-110.jpg",
      "layout_category": "mujer",
      "text": "El director de ciencias de la NASA pidió cautela, recordando que el universo tiene fenómenos naturales extremos que aún no comprendemos del todo.",
      "voice": "mujer_1",
      "bgm_mood": "analisis",
      "sfx_type": "transiciones"
    },
    {
      "type": "pexels",
      "termino_busqueda": "galaxy stars",
      "layout_category": "sin_presentador",
      "text": "¿Crees que estamos solos en el universo o que hemos encontrado a alguien? Déjanos tu opinión en los comentarios ahora mismo.",
      "voice": "hombre_1",
      "bgm_mood": "tension",
      "sfx_type": "impactos"
    }
  ]
}

    resultado = process_video_payload(payload)

    print("\n" + "="*70)
    if resultado:
        print(f"  ¡NOTICIERO SHORT MULTI-ANUNCIO CREADO EXITOSAMENTE!\n  Archivo guardado en: {resultado}")
    else:
        print("  LA PRUEBA HA FALLADO. Revisa los logs arriba para ver el error.")
    print("="*70 + "\n")

if __name__ == "__main__":
    ejecutar_prueba_multianuncio()