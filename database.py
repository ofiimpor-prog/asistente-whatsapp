import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Obtener la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

# PARCHE CRÍTICO: Si la URL viene de Render, corregimos el protocolo
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

Base = declarative_base()

class Transaccion(Base):
    __tablename__ = 'transacciones'
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    tipo = Column(String)    # 'ingreso' o 'egreso'
    monto = Column(Float)
    descripcion = Column(String)
    fecha = Column(DateTime, default=datetime.now)

class Recordatorio(Base):
    __tablename__ = 'recordatorios'
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    contenido = Column(String)
    fecha_recordatorio = Column(DateTime)
    estado = Column(String, default="pendiente")

# Configuración del motor con el parche aplicado
engine = create_engine(DATABASE_URL if DATABASE_URL else "sqlite:///asistente.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def inicializar_db():
    Base.metadata.create_all(bind=engine)
