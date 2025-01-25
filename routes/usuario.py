import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Annotated
from config.db import engine, SessionLocal
from models.usuario import Usuario
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

@router_usuario.post("/usuarios", status_code=status.HTTP_201_CREATED)
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