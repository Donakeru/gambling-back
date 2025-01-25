import uuid
from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP
from sqlalchemy.sql import func
from config.db import Base, engine

class Usuario(Base):
    __tablename__ = 'Usuario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), nullable=False, unique=True, server_default=func.uuid())  # Genera el valor en el DDL
    nickname = Column(String(50), nullable=False, unique=True)
    saldo_actual = Column(DECIMAL(10, 2), nullable=False, server_default="2000.00")  # Valor predeterminado en la base de datos
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp())  # Timestamp gestionado por la base de datos
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

# Crear el esquema en la base de datos
Base.metadata.create_all(engine)