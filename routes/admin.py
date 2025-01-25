import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DataError
from typing import Annotated
from config.db import engine, SessionLocal
from models.global_models import Apuesta
from schemas.admin import CrearSalaBaseModel, CerrarSalaBaseModel

router_admin = APIRouter(
    prefix="/admin",
    tags=["admin"],
)
# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router_admin.post("/sala")
async def crear_sala(sala: CrearSalaBaseModel,db: db_dependency):
    db_registro = Apuesta(codigo_sala=sala.codigo_sala, id_juego=sala.id_juego)
    try:
        db.add(db_registro)
        db.commit()
        db.refresh(db_registro)
        return {"status": "OK"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El código de sala '{sala.codigo_sala}' ya se ha usado."
        )
    except DataError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error en los datos ingresados, verifique los valores."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )
        
@router_admin.patch("/sala")
async def cerrar_sala(sala: CerrarSalaBaseModel, db: db_dependency):
    # Verificar si la sala existe
    sala_db = db.query(Apuesta).filter(Apuesta.codigo_sala == sala.codigo_sala).first()
    
    if not sala_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sala no encontrada")
    
    # Verificar si la sala ya está cerrada
    if not sala_db.is_abierta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La sala ya está cerrada")
    
    # Cerrar la sala
    sala_db.is_abierta = False
    db.commit()
    
    # TODO: SIMULACIÓN APUESTA, REGISTRO DE RESULTADOS Y REPARTICION DE GANANCIAS

    return {"mensaje": "Sala cerrada exitosamente"}