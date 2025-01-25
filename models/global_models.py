from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, ForeignKey, UniqueConstraint, DateTime, Boolean
from sqlalchemy.sql import func
from config.db import Base, engine
from sqlalchemy.orm import relationship

class Usuario(Base):
    __tablename__ = 'Usuario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), nullable=False, unique=True, server_default=func.uuid())  # Genera el valor en el DDL
    nickname = Column(String(50), nullable=False, unique=True)
    saldo_actual = Column(DECIMAL(10, 2), nullable=False, server_default="2000.00")  # Valor predeterminado en la base de datos
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())  # Timestamp gestionado por la base de datos
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
class Juegos(Base):
    __tablename__ = 'Juegos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_juego = Column(String(100), nullable=False, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)

    opciones_apuesta = relationship("OpcionesApuestaJuegos", back_populates="juego", cascade="all, delete, delete-orphan")
    apuestas = relationship("Apuesta", back_populates="juego", cascade="all, delete, delete-orphan")

class OpcionesApuestaJuegos(Base):
    __tablename__ = 'Opciones_Apuesta_Juegos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_opcion = Column(String(100), nullable=False)
    id_Juego = Column(Integer, ForeignKey('Juegos.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)

    juego = relationship("Juegos", back_populates="opciones_apuesta")

class Apuesta(Base):
    __tablename__ = 'Apuesta'

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_sala = Column(String(8), nullable=False, unique=True)
    is_abierta = Column(Boolean, default=True)
    resultado = Column(Integer, ForeignKey('Opciones_Apuesta_Juegos.id', ondelete="RESTRICT", onupdate="CASCADE"), nullable=True)
    id_juego = Column(Integer, ForeignKey('Juegos.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)

    juego = relationship("Juegos", back_populates="apuestas")
    opcion_apuesta = relationship("OpcionesApuestaJuegos")

# Crear el esquema en la base de datos
Base.metadata.create_all(engine)