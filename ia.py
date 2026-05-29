from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from acta import ActaElectoral
from partidos import Partido
import os
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

    if tabla_ia and tabla_ia.get('type') == 'array' and 'valueArray' in tabla_ia:
        for row in tabla_ia['valueArray']:
       
            obj = row.get('valueObject', {})
            nombre_field = obj.get('nombre_partido')
            votos_field = obj.get('votos')

            if nombre_field and votos_field:
                p_nombre = nombre_field.get('valueString', 'Desconocido')
                votos_raw = votos_field.get('valueString', '0')
                p_votos = int(votos_raw) if votos_raw.isdigit() else 0
                partidos_extraidos.append(Partido(p_nombre, p_votos))

    return nueva_acta, partidos_extraidos, id_qr


if __name__ == "__main__":
    url = "https://www.ieem.org.mx/prep2024/actas/AYU_5672_001.jpg"
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