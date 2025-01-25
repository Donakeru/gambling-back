from pydantic import BaseModel

class CrearSalaBaseModel(BaseModel):
    codigo_sala: str
    id_juego: int
    
class CerrarSalaBaseModel(BaseModel):
    codigo_sala: str