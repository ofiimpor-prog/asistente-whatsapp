import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# En Render, crea una Database PostgreSQL y pega el Internal Database URL en tus env vars
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")

Base = declarative_base()

class Transaccion(Base):
    __tablename__ = 'transacciones'
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    tipo = Column(String) # ingreso o egreso
    monto = Column(Float)
    descripcion = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)

class Recordatorio(Base):
    __tablename__ = 'recordatorios'
    id = Column(Integer, primary_key=True)
    usuario = Column(String)
    evento = Column(String)
    fecha_hora = Column(DateTime)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def inicializar_db():
    Base.metadata.create_all(bind=engine)
