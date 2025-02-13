from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "mysql+pymysql://root:NicolasEsteban32!@localhost:3306/db_lets_go_gambling"

#db_lets_go_gambling
# Crear motor de SQLAlchemy
engine = create_engine(DATABASE_URL, pool_size=3, max_overflow=0)

# Definir la base para los modelos de SQLAlchemy
Base = declarative_base()

# Crear la sesión de SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)