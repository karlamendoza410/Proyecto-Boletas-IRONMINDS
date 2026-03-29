from acta import ActaElectoral
from ia import procesar_acta_con_ia
from partidos import Partido


def flujo_principal(lista_imagenes):
   
    acumulador_votos = {}
    for ruta in lista_imagenes:
        print(f"\n--- Procesando: {ruta} ---")
        acta, partidos_extraidos, folio = procesar_acta_con_ia(ruta)
   


        print(f"\n--- REPORTE DE ACTAS DE CASILLA (FOLIO: {folio}) ---")
        print(acta.generar_reporte(partidos_extraidos))



        resultado = acta.validar_acta(partidos_extraidos)
    
        if "Acta válida" in resultado:
            print("La suma coincide con el total.")
            print(acta.validar_firma())
        else:
            print(f" ERROR: {resultado}")

        for p in partidos_extraidos:
            nombre = p.nombre_partido
            votos = p.votos
            acumulador_votos[nombre] = acumulador_votos.get(nombre, 0) + votos


if __name__ == "__main__":

    imagenes = [
        "/Users/axelcorona/Downloads/DIP_5664_003.jpg",   
        "/Users/axelcorona/Downloads/DIP_5665_002.jpg",
        "/Users/axelcorona/Downloads/DIP_5666_001.jpg",
        "/Users/axelcorona/Downloads/DIP_5666_002.jpg",
        "/Users/axelcorona/Downloads/DIP_5668_005.jpg",
        "/Users/axelcorona/Downloads/DIP_5670_001.jpg",
        "/Users/axelcorona/Downloads/DIP_5670_002.jpg",
        "/Users/axelcorona/Downloads/DIP_5671_001.jpg",
        "/Users/axelcorona/Downloads/DIP_5671_002.jpg",
        "/Users/axelcorona/Downloads/DIP_5672_001.jpg",
        "/Users/axelcorona/Downloads/DIP_5672_002.jpg",
        "/Users/axelcorona/Downloads/DIP_5675_001.jpg",
        "/Users/axelcorona/Downloads/DIP_5674_002.jpg",
        "/Users/axelcorona/Downloads/DIP_5674_001.jpg",
        "/Users/axelcorona/Downloads/DIP_5673_052.jpg",
        "/Users/axelcorona/Downloads/DIP_5672_004.jpg",
        "/Users/axelcorona/Downloads/DIP_5673_002.jpg",
        "/Users/axelcorona/Downloads/DIP_5673_001.jpg",
        "/Users/axelcorona/Downloads/DIP_5672_003.jpg",
        "/Users/axelcorona/Downloads/DIP_5673_050.jpg",
        "/Users/axelcorona/Downloads/DIP_5673_003.jpg"
    ]          

flujo_principal(imagenes)