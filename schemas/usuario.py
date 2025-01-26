from pydantic import BaseModel

class UsuarioBaseModel(BaseModel):
    nickname: str
    
class ApuestaUsuarioBaseModel(BaseModel):
    uuid_usuario: str
    codigo_sala: str
    opcion_apuesta: int
    monto_apuesta: float