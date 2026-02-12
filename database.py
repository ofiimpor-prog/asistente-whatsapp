import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

# Parche para compatibilidad con Render
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

Base = declarative_base()

class Transaccion(Base):
    __tablename__ = 'transacciones'
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    tipo = Column(String) 
    monto = Column(Float)
    descripcion = Column(String)
    fecha = Column(DateTime, default=datetime.now)

class Recordatorio(Base):
    __tablename__ = 'recordatorios'
    id = Column(Integer, primary_key=True)
    usuario = Column(String) # Aquí guardaremos el número de destino
    contenido = Column(String)
    fecha_recordatorio = Column(DateTime)
    estado = Column(String, default="pendiente")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def inicializar_db():
    Base.metadata.create_all(bind=engine)
