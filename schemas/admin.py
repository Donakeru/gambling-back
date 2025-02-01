from pydantic import BaseModel

class CrearSalaBaseModel(BaseModel):
    id_juego: int
    
class CerrarSalaBaseModel(BaseModel):
    codigo_sala: str