from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from acta import ActaElectoral
from partidos import Partido
import os
import re
import requests


def procesar_acta_con_ia(ruta):
    

    model_id = "Analizador_ACTAS" 
    
    client = DocumentIntelligenceClient(endpoint="", credential = AzureKeyCredential(""))

    with open(ruta, "rb") as f:
        
        poller = client.begin_analyze_document(model_id, body=f, content_type="application/octet-stream")
        result = poller.result()

    campos = result.documents[0].fields
    

    id_qr = campos.get("QR").content if campos.get("QR") else "Sin_QR"


    nueva_acta = ActaElectoral(
        municipio=campos.get("municipio").content if campos.get("municipio") else "N/A",
        seccion=int(campos.get("seccion").content) if campos.get("seccion") and campos.get("seccion").content.isdigit() else 0,
        tipo_casilla=campos.get("tipo_casilla").content if campos.get("tipo_casilla") else "N/A",
        total_votos=int(campos.get("total_votos").content) if campos.get("total_votos") and campos.get("total_votos").content and campos.get("total_votos").content.isdigit() else 0,
        firma=True
    )

    partidos_extraidos = []
    tabla_ia = campos.get("tabla_resultados")

    ordenPartidos = [
        "PAN",
        "Partido Verde",
        "PT",
        "Movimiento Ciudadano",
        "Morena",
        "Coalición PT-Verde-Morena",
        "Coalición PT-Verde",
        "Coalición Verde-Morena",
        "Coalición PT-Morena",
        "CANDIDATOS NO REGISTRADOS",
        "VOTOS NULOS"
    ]

    if tabla_ia and tabla_ia.get('type') == 'array' and 'valueArray' in tabla_ia:
        indice_partido = 0

        for row in tabla_ia['valueArray']:
            if indice_partido >= len(ordenPartidos):
                break

            obj = row.get('valueObject', {})
            votos_field = obj.get('votos')

            if not votos_field:
                continue

            votos_raw = str(votos_field.get('valueString', '')).upper()
            lineas = votos_raw.split('\n')

            for linea in lineas:
                if indice_partido >= len(ordenPartidos):
                    break

                linea = linea.replace('O', '0')
                votos_limpios = re.sub(r'\D', '', linea)

                if not votos_limpios:
                    continue

                if len(votos_limpios) > 3:
                    pedazos = [votos_limpios[i:i+3] for i in range(0, len(votos_limpios), 3)]
                    for pedazo in pedazos:
                        if indice_partido >= len(ordenPartidos):
                            break
                        partidos_extraidos.append(Partido(ordenPartidos[indice_partido], int(pedazo)))
                        indice_partido += 1
                else:
                    partidos_extraidos.append(Partido(ordenPartidos[indice_partido], int(votos_limpios)))
                    indice_partido += 1
        while indice_partido < len(ordenPartidos):
            partidos_extraidos.append(Partido(ordenPartidos[indice_partido], 0))
            indice_partido += 1

    return nueva_acta, partidos_extraidos, id_qr
if __name__ == "__main__":
    url = "https://www.ieem.org.mx/prep2024/actas/AYU_5662_002.jpg"
    ruta = "acta5672.jpg"

    print("descargando imagen")
    respuesta = requests.get(url)
    
    if respuesta.status_code == 200:
        with open(ruta, "wb") as archivo:
            archivo.write(respuesta.content)
            
        print("procesando")
        acta, partidos_extraidos, folio = procesar_acta_con_ia(ruta)
        
        print(f"Reporte del Acta {folio}:")
        print(acta.generar_reporte())
        os.remove(ruta)
    else:
        print("error al descargar imagen")