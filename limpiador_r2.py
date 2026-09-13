import os
import boto3
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Cargar las credenciales de tu archivo .env local
load_dotenv()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

def limpiar_bucket_r2(dias_antiguedad=28):
    print("==================================================")
    print(" INICIANDO LIMPIEZA MASIVA EN CLOUDFLARE R2")
    print("==================================================")

    # Conectar a R2 usando boto3
    s3 = boto3.client(
        's3',
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name="auto"
    )

    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias_antiguedad)
    print(f"[*] Buscando archivos modificados antes de: {fecha_limite.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=R2_BUCKET_NAME)

    archivos_borrados = 0
    bytes_liberados = 0

    try:
        for page in pages:
            if 'Contents' in page:
                lote_a_borrar = []
                
                for obj in page['Contents']:
                    if obj['LastModified'] < fecha_limite:
                        # Guardamos el archivo para el borrado en lote y sumamos su peso
                        lote_a_borrar.append({'Key': obj['Key']})
                        bytes_liberados += obj['Size']
                        archivos_borrados += 1
                        
                        # Mostrar en consola qué archivo se detectó (opcional, puedes comentarlo si es mucho texto)
                        print(f"🗑️ Marcado para borrar: {obj['Key']} ({obj['Size'] / (1024*1024):.2f} MB)")

                # La API permite borrar de a 1000 archivos por petición
                if lote_a_borrar:
                    for i in range(0, len(lote_a_borrar), 1000):
                        batch = lote_a_borrar[i:i+1000]
                        s3.delete_objects(
                            Bucket=R2_BUCKET_NAME,
                            Delete={'Objects': batch}
                        )
                        print(f"\n[+] Lote de {len(batch)} archivos eliminado físicamente.\n")

    except Exception as e:
        print(f"\n❌ Error al comunicarse con Cloudflare R2: {e}")
        return

    # Convertir los bytes a Gigabytes
    gb_liberados = bytes_liberados / (1024 ** 3)

    print("==================================================")
    print(" RESUMEN DE LA LIMPIEZA COMPLETADA")
    print("==================================================")
    print(f"📄 Total de archivos eliminados : {archivos_borrados}")
    print(f"💾 Espacio total liberado       : {gb_liberados:.2f} GB")
    print("==================================================")

if __name__ == '__main__':
    limpiar_bucket_r2(dias_antiguedad=28)