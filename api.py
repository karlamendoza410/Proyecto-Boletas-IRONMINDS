from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import requests
import os
import uuid
from ia import procesar_acta_con_ia 

app = FastAPI()
class PeticionImagen(BaseModel):
    url: str

@app.post("/procesar-acta")
async def procesar(peticion: PeticionImagen):
    ruta = f"temp_{uuid.uuid4().hex}.jpg"
    
    try:
        print(f"descargando imagen de: {peticion.url}")
        respuesta_http = requests.get(peticion.url, timeout=15)
        respuesta_http.raise_for_status() 
        
        with open(ruta, "wb") as archivo:
            archivo.write(respuesta_http.content)
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"No se pudo descargar la imagen. Verifica la URL. Detalles: {str(e)}")

    try:
        acta_obj, partidos_extraidos, folio_qr = procesar_acta_con_ia(ruta)
        
        diccionario_votos = {}
        for p in partidos_extraidos:
            diccionario_votos[p.nombre_partido] = p.votos 

        respuesta = {
            "tipo_eleccion": 2, 
            "distrito": 14, 
            "municipio": acta_obj.municipio,
            "seccion": str(acta_obj.seccion).zfill(3),
            "tipo_casilla": acta_obj.tipo_casilla,
            "total_votos": acta_obj.total_votos,
            "votos_partido": diccionario_votos,
            "votos_nulos": 0, 
            "qr_data": folio_qr,
            "fecha_procesamiento": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        return respuesta
        
    except Exception as e:
        print(f"error procesando el acta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"error interno procesando el acta: {str(e)}")
        
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)