from decimal import Decimal
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.sql import func
from typing import Annotated
from config.db import engine, SessionLocal
from models.global_models import Apuesta, OpcionesApuestaJuegos, ApuestaUsuario, Usuario
from schemas.admin import CrearSalaBaseModel, CerrarSalaBaseModel
from prolog.evento_ruleta import tirar_ruleta, ganancia, generar_codigo_sala


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
    try:
        
        codigo_sala = generar_codigo_sala()

        db_registro = Apuesta(codigo_sala=codigo_sala, id_juego=sala.id_juego)
        db.add(db_registro)
        db.commit()
        return {"status": "OK", "codigo_sala": codigo_sala}
    
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
    
    resultado_ruleta = tirar_ruleta()
    
    # Buscar el primer registro que coincida
    id_opcion_resultado = db.query(OpcionesApuestaJuegos).filter(
        OpcionesApuestaJuegos.nombre_opcion.ilike(resultado_ruleta),
        OpcionesApuestaJuegos.id_Juego == sala_db.id_juego
    ).first()

    # Validar si se encontró el registro
    if not id_opcion_resultado:
        raise HTTPException(status_code=404, detail="No se encontró ninguna opción de apuesta con los criterios especificados.")
    
    # Cerrar la sala
    sala_db.is_abierta = False
    sala_db.resultado = id_opcion_resultado.id
    
    jugadores_ganadores = db.query(ApuestaUsuario).filter(
        ApuestaUsuario.id_apuesta == sala_db.id,
        ApuestaUsuario.opcion_apuesta == id_opcion_resultado.id
    ).all()
    
    # Realizar la consulta para obtener la suma de los puntos apostados por los ganadores
    suma_valores_ganadores = db.query(func.sum(ApuestaUsuario.monto_apostado)).filter(
        ApuestaUsuario.id_apuesta == sala_db.id,
        ApuestaUsuario.opcion_apuesta == id_opcion_resultado.id
    ).scalar()
    
    # Realizar la consulta para obtener la suma de los puntos apostados por todos los jugadores
    suma_valores_totales = db.query(func.sum(ApuestaUsuario.monto_apostado)).filter(
        ApuestaUsuario.id_apuesta == sala_db.id
    ).scalar()
    
    # Itera y actualiza el valor de las columnas
    for ganador in jugadores_ganadores:
        
        monto_ganado = ganancia(ganador.monto_apostado, suma_valores_ganadores, suma_valores_totales)
        
        ganador.is_gano = True
        ganador.monto_ganado = monto_ganado
        
        usuario = db.query(Usuario).filter(Usuario.id == ganador.id_usuario).first()
        
        usuario.saldo_actual += Decimal(monto_ganado)
    
    db.commit()
    
    # TODO: Y REPARTICION DE GANANCIAS
    return {"mensaje": f"Sala cerrada y el resultado ganador de la apuesta fue: {id_opcion_resultado.nombre_opcion}"}

@router_admin.get("/test")
def prueba(db: db_dependency):
    return generar_codigo_sala()