from fastapi import FastAPI, UploadFile, File
import pandas as pd
import numpy as np
import shutil
import os


from ia import procesar_acta_con_ia

app = FastAPI(title="Sistema de Escrutinio Electoral IA")


base_datos_votos = []


@app.post("/escanear-acta/")
async def escanear_acta(file: UploadFile = File(...)):

    ruta_temporal = f"temp_{file.filename}"
    with open(ruta_temporal, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:

        acta, partidos_extraidos, folio = procesar_acta_con_ia(ruta_temporal)


        validacion = acta.validar_acta(partidos_extraidos)

        if "Error" in validacion:
            return {"status": "error", "mensaje": validacion, "folio": folio}


        for p in partidos_extraidos:
            base_datos_votos.append({
                "folio": folio,
                "municipio": acta.municipio,
                "seccion": acta.seccion,
                "partido": p.nombre_partido,
                "votos": p.votos
            })

        return {
            "status": "ok",
            "folio": folio,
            "municipio": acta.municipio,
            "reporte": acta.generar_reporte(partidos_extraidos)
        }

    finally:

        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@app.get("/resultados-globales/")
def obtener_resultados_globales():
    #pandas numpy
    if not base_datos_votos:
        return {"mensaje": "No hay actas procesadas aún."}


    df = pd.DataFrame(base_datos_votos)


    votos_por_partido = df.groupby("partido")["votos"].sum().reset_index()


    total_votos_general = np.sum(votos_por_partido["votos"].values)

    votos_por_partido["porcentaje"] = np.round((votos_por_partido["votos"] / total_votos_general) * 100, 2)

    resultados = votos_por_partido.to_dict(orient="records")

    return {
        "total_actas_procesadas": len(df["folio"].unique()),
        "total_votos_emitidos": int(total_votos_general),
        "conteo_por_partido": resultados
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)