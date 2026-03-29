from abc import ABC, abstractmethod
from partidos import Partido

class ActaBase(ABC):
    def __init__(self, municipio: str, seccion: int, tipo_casilla: str, total_votos: int, firma: bool):
        self.municipio = municipio
        self.seccion = seccion
        self.tipo_casilla = tipo_casilla
        self.total_votos = total_votos
        self.firma = firma

    @abstractmethod
    def validar_acta(self):

        pass

    @abstractmethod
    def generar_reporte(self):
       
        pass


class ActaElectoral(ActaBase):
    def validar_acta(self, lista_partidos):
        suma_de_votos = sum(partido.votos for partido in lista_partidos)
        if self.total_votos != suma_de_votos:
            return "Error: Los votos no coinciden."
        return "Acta válida."

    def generar_reporte(self, lista_partidos):
        votos_str = ', '.join(f'{p.nombre_partido}: {p.votos}' for p in lista_partidos)
        return (f"Municipio: {self.municipio} | Sección: {self.seccion} | "
        f"Casilla: {self.tipo_casilla} | Total de votos: {self.total_votos} | "
        f"Votos por partido: [{votos_str}]")

    def validar_firma(self): 
        if not self.firma ==  True:
            raise ValueError("El acta no contiene todas las firmas necesarias, revisa de nuevo.")
        return "Firmas validas"