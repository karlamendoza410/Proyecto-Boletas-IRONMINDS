import requests

url_api = "http://127.0.0.1:8000/procesar-acta"
datos_peticion = {
    "url": "https://www.ieem.org.mx/prep2024/actas/AYU_5672_001.jpg"
}

print("consultando a la api (por favor espera)")
respuesta = requests.post(url_api, json=datos_peticion)

if respuesta.status_code == 200:
    json_acta = respuesta.json()
    votos = json_acta["votos_partido"]