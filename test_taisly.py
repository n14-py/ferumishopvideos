import requests
import json

# ===== CONFIGURACIÓN =====
API_KEY = "taisly_dc97bfef8a1e9ae497d86440d8185f4d42f5f5ce138f1251c6e26654880566a8"
BASE_URL = "https://app.taisly.com/api/private"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# ===== CONSULTAR CUENTAS =====
response = requests.get(
    f"{BASE_URL}/platform/platforms",
    headers=headers
)

print(f"Código HTTP: {response.status_code}")

if response.status_code != 200:
    print(response.text)
    exit()

data = response.json()

print("\n===== RESPUESTA COMPLETA =====\n")
print(json.dumps(data, indent=4, ensure_ascii=False))

print("\n===== CUENTAS CONECTADAS =====\n")

platforms = data.get("data", [])

if not platforms:
    print("No hay cuentas conectadas.")
    exit()

for i, account in enumerate(platforms, start=1):
    print(f"Cuenta #{i}")
    print("-" * 50)

    for key, value in account.items():
        print(f"{key}: {value}")

    print()