from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import os
import requests
import uuid 

from ia import procesar_acta_con_ia

app = FastAPI(title="Sistema de conteo de actas")

base_datos_votos = []

class PeticionImagen(BaseModel):
    url: str

@app.post("/escanear-acta/")
def escanear_acta(datos: PeticionImagen):
    ruta_temporal = f"temp_{uuid.uuid4().hex}.jpg"
    
    try:
        cabeceras = {"user-agent": "mozilla/5.0"}
        respuesta_http = requests.get(datos.url, headers=cabeceras, timeout=20)
        respuesta_http.raise_for_status()

        with open(ruta_temporal, "wb") as buffer:
            buffer.write(respuesta_http.content)
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al descargar la imagen: {str(e)}")
        
    try:
        acta, partidos_extraidos, folio = procesar_acta_con_ia(ruta_temporal)
        validacion = acta.validar_acta(partidos_extraidos)

        if "Error" in validacion:
            suma_calculada = sum(p.votos for p in partidos_extraidos)
            total_leido = getattr(acta, 'total_votos', 'No encontrado')
            
            detalle_votos = ""
            for p in partidos_extraidos:
                detalle_votos += f"\n- {p.nombre_partido}: {p.votos}"
                
            mensaje_debug = (
                f"{validacion}\n"
                f"Suma calculada: {suma_calculada} | Total leido en acta: {total_leido}\n"
                f"Desglose de azure:{detalle_votos}"
            )
            
            return {"status": "error", "mensaje": mensaje_debug, "folio": folio}

        for p in partidos_extraidos:
            nombre = str(p.nombre_partido).strip()
            if nombre in ["?", "&", "Desconocido"] or len(nombre) <= 1 or nombre.isdigit():
                continue 
            if p.votos == 0 and "CANDIDATOS" not in nombre.upper():
                continue
                
            base_datos_votos.append({
                "folio": folio,
                "municipio": acta.municipio,
                "seccion": acta.seccion,
                "partido": nombre, 
                "votos": p.votos
            })

        return {
            "status": "ok",
            "folio": folio,
            "municipio": acta.municipio,
            "reporte": acta.generar_reporte(partidos_extraidos)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno procesando el acta: {str(e)}")
    
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@app.get("/resultados-globales/")
def obtener_resultados_globales():
    if not base_datos_votos:
        return {"mensaje": "No hay actas procesadas aun"}

    df = pd.DataFrame(base_datos_votos)
    votos_por_partido = df.groupby("partido")["votos"].sum().reset_index()
    total_votos_general = np.sum(votos_por_partido["votos"].values)

    if total_votos_general > 0:
        votos_por_partido["porcentaje"] = np.round((votos_por_partido["votos"] / total_votos_general) * 100, 2)
    else:
        votos_por_partido["porcentaje"] = 0.0

    resultados = votos_por_partido.to_dict(orient="records")

    return {
        "total_actas_procesadas": len(df["folio"].unique()),
        "total_votos_emitidos": int(total_votos_general),
        "conteo_por_partido": resultados
    }

@app.delete("/reiniciar-conteo/")
def reiniciar_conteo():
    global base_datos_votos 
    base_datos_votos.clear()
    return {"status": "ok", "mensaje": "Base de datos reiniciada con exito"}

@app.delete("/reiniciar-conteo/")
def reiniciar_conteo():
    global base_datos_votos 
    base_datos_votos.clear()
    return {"status": "ok", "mensaje": "Base de datos reiniciada con exito"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)