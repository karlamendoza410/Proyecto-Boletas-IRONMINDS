class Partido:
    def __init__(self, nombre_partido: str, votos: int):
         self.nombre_partido = nombre_partido
         self.votos = votos
         

    def __str__(self):
        return f"{self.nombre_partido}: {self.votos}"
    
   
    def agregar_a_lista(self):
        global partidos_y_votos
        partidos_y_votos.append(self)
        