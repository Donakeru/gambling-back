import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Annotated
from config.db import engine, SessionLocal
from models.global_models import Usuario, OpcionesApuestaJuegos, Apuesta, Juegos
from schemas.usuario import UsuarioBaseModel

router_usuario = APIRouter()

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router_usuario.get("/usuarios")
async def get_usuarios(db:db_dependency):
    registros = db.query(Usuario).all()
    return registros

@router_usuario.post("/usuario", status_code=status.HTTP_201_CREATED)
async def create_usuarios(usuario: UsuarioBaseModel, db:db_dependency):
    # Crear el registro en la base de datos
    db_registro = Usuario(nickname=usuario.nickname)
    try:
        db.add(db_registro)
        db.commit()
        db.refresh(db_registro)  # Actualiza el objeto con los datos de la base de datos

        # Retornar el registro recién creado
        return {"status": "OK", "uuid": db_registro.uuid}
    except IntegrityError:
        db.rollback()  # Revertir la transacción en caso de error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nickname '{usuario.nickname}' ya está en uso."
        )
        
@router_usuario.get('/usuario/{uuid}', status_code=status.HTTP_200_OK)
async def consultar_usuario_por_uuid(uuid: str, db: db_dependency):
    try:
        # Consultamos el usuario en la base de datos
        registro = db.query(Usuario).filter(Usuario.uuid == uuid).first()

        if not registro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con UUID {uuid} no encontrado."
            )

        # Convertimos el registro en un diccionario y excluimos el campo 'id'
        usuario_dict = {
            key: value for key, value in registro.__dict__.items() 
            if key != 'id' and not key.startswith('_')
        }

        return usuario_dict
    except Exception as e:
        # Capturamos cualquier error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar el usuario: {str(e)}"
        )
        
@router_usuario.get('/sala/{codigo_sala}', status_code=status.HTTP_200_OK)
async def consultar_sala_por_codigo(codigo_sala: str, db: db_dependency):
    try:
        # Consultamos el registro de la sala en la base de datos
        registro = db.query(Apuesta).filter(Apuesta.codigo_sala == codigo_sala).first()

        if not registro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La sala {codigo_sala} no se ha encontrado."
            )
            
        # Verificar si la sala ya está cerrada
        if not registro.is_abierta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La sala ya está cerrada"
            )

        # Obtener el juego asociado a la sala
        juego = db.query(Juegos).filter(Juegos.id == registro.id_juego).first()

        if not juego:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El juego asociado a la sala no se ha encontrado."
            )

        # Obtener las opciones de apuesta asociadas al juego
        opciones_apuesta = db.query(OpcionesApuestaJuegos).filter(
            OpcionesApuestaJuegos.id_Juego == juego.id
        ).all()

        # Convertimos las opciones a una lista de diccionarios con solo id y nombre_opcion
        opciones_dict = [
            {"id": opcion.id, "nombre_opcion": opcion.nombre_opcion}
            for opcion in opciones_apuesta
        ]
        
        sala_dict = {
            key: value for key, value in registro.__dict__.items()
            if key != 'id' and not key.startswith('_') and key != 'id_juego' and key != 'resultado'
        }

        # Añadimos el nombre del juego al diccionario de la sala
        sala_dict["nombre_juego"] = juego.nombre_juego

        # Añadimos las opciones al diccionario de la sala
        sala_dict["opciones_apuesta"] = opciones_dict

        return sala_dict
    except Exception as e:
        # Capturamos cualquier error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar la sala: {str(e)}"
        )
