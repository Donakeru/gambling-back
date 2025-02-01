import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Annotated
from config.db import engine, SessionLocal
from models.global_models import Usuario, OpcionesApuestaJuegos, Apuesta, Juegos, ApuestaUsuario
from schemas.usuario import UsuarioBaseModel, ApuestaUsuarioBaseModel

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
        usuario = db.query(Usuario).filter(Usuario.uuid == uuid).first()

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con UUID {uuid} no encontrado."
            )

        # Consultamos el historial de apuestas del usuario
        historial_apuestas = []
        apuestas_usuario = db.query(ApuestaUsuario).filter(ApuestaUsuario.id_usuario == usuario.id).all()

        for apuesta_usuario in apuestas_usuario:
            info_apuesta = db.query(Apuesta).filter(Apuesta.id == apuesta_usuario.id_apuesta).first()
            info_juego = db.query(Juegos).filter(Juegos.id == info_apuesta.id_juego).first()
            apuesta = {
                "codigo_sala": apuesta_usuario.apuesta.codigo_sala,
                "monto_apostado": apuesta_usuario.monto_apostado,
                "is_sala_abierta": info_apuesta.is_abierta,
                "juego": info_juego.nombre_juego,
                "opcion_apuesta": apuesta_usuario.opcion_apuesta_rel.nombre_opcion,
                "is_gano": apuesta_usuario.is_gano,
                "fecha": apuesta_usuario.created_at
            }
            historial_apuestas.append(apuesta)

        # Convertimos el registro de usuario en un diccionario y excluimos el campo 'id'
        usuario_dict = {
            key: value for key, value in usuario.__dict__.items() 
            if key != 'id' and not key.startswith('_')
        }

        # Agregamos el historial de apuestas al diccionario del usuario
        usuario_dict["historial_apuestas"] = historial_apuestas

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

@router_usuario.post('/sala/apostar', status_code=status.HTTP_201_CREATED)
async def entrar_en_apuesta(apuesta_usuario: ApuestaUsuarioBaseModel, db: db_dependency):
    try:
        # VALIDACIONES -----
        
        # 1. Verificar si el usuario existe
        usuario = db.query(Usuario).filter(Usuario.uuid == apuesta_usuario.uuid_usuario).first()
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # 2. Verificar si la sala existe
        apuesta = db.query(Apuesta).filter(Apuesta.codigo_sala == apuesta_usuario.codigo_sala, Apuesta.is_abierta == True).first()
        if not apuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sala no encontrada o ya se ha cerrado"
            )
            
        # 3. Verificar si el usuario ya tiene una apuesta en esa sala
        apuesta_existente = db.query(ApuestaUsuario).join(Apuesta).filter(
            ApuestaUsuario.id_usuario == usuario.id,
            Apuesta.codigo_sala == apuesta_usuario.codigo_sala
        ).first()
        
        if apuesta_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya has realizado una apuesta en esta sala"
            )

        # 4. Verificar si la opción de apuesta es válida
        opcion_apuesta = db.query(OpcionesApuestaJuegos).filter(OpcionesApuestaJuegos.id == apuesta_usuario.opcion_apuesta).first()
        if not opcion_apuesta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opción de apuesta no válida"
            )

        # 5. Verificar si el monto apostado es mayor que 200
        if apuesta_usuario.monto_apuesta <= 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto de la apuesta debe ser mayor a 200"
            )
            
        # 6. Verificar si el monto apostado NO es mayor al saldo actual
        if apuesta_usuario.monto_apuesta > usuario.saldo_actual:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto de la apuesta es superior al disponible"
            )
            
        # REGISTRO Y CONFIRMACIÓN DE LA APUESTA ---
        nueva_apuesta_usuario = ApuestaUsuario(
            id_usuario=usuario.id,
            id_apuesta=apuesta.id,
            opcion_apuesta=apuesta_usuario.opcion_apuesta,
            monto_apostado=apuesta_usuario.monto_apuesta,
            is_gano=False 
        )
        
        # Restar el monto apostado del saldo actual del usuario
        usuario.saldo_actual -= Decimal(apuesta_usuario.monto_apuesta)
        
        # Agregar el registro de la apuesta y actualizar el saldo
        db.add(nueva_apuesta_usuario)
        db.commit()

        return {"message": "Apuesta registrada correctamente"}
    
    except SQLAlchemyError as e:
        db.rollback()  # Hacer rollback en caso de error en la base de datos
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la apuesta: {str(e)}"
        )
        
    except Exception as e:
        # Capturamos cualquier error inesperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar la sala: {str(e)}"
        )
