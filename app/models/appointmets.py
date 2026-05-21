from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Cita(Base):
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id", ondelete="RESTRICT"), nullable=False)
    fecha_hora = Column(DateTime, nullable=False)
    estado = Column(String(20), nullable=False, default="pendiente")
    motivo = Column(Text, nullable=False)

    historia_clinica = relationship("HistoriaClinica", back_populates="cita", uselist=False)


class HistoriaClinica(Base):
    __tablename__ = "historias_clinicas"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id", ondelete="RESTRICT"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id", ondelete="RESTRICT"), nullable=False)
    cita_id = Column(Integer, ForeignKey("citas.id", ondelete="SET NULL"), unique=True, nullable=True)
    fecha_creacion = Column(DateTime, nullable=False)
    sintomas = Column(Text, nullable=False)
    diagnostico = Column(Text, nullable=False)

    cita = relationship("Cita", back_populates="historia_clinica")
    recetas = relationship("Receta", back_populates="historia_clinica", cascade="all, delete-orphan")


class Receta(Base):
    __tablename__ = "recetas"

    id = Column(Integer, primary_key=True, index=True)
    historia_clinica_id = Column(Integer, ForeignKey("historias_clinicas.id", ondelete="CASCADE"), nullable=False)
    fecha_emision = Column(DateTime, nullable=False)
    indicaciones_generales = Column(Text, nullable=True)

    historia_clinica = relationship("HistoriaClinica", back_populates="recetas")
    detalles = relationship("DetalleReceta", back_populates="receta", cascade="all, delete-orphan")


class DetalleReceta(Base):
    __tablename__ = "detalle_recetas"

    id = Column(Integer, primary_key=True, index=True)
    receta_id = Column(Integer, ForeignKey("recetas.id", ondelete="CASCADE"), nullable=False)
    medicamento = Column(String(150), nullable=False)
    dosis = Column(String(100), nullable=False)
    frecuencia = Column(String(100), nullable=False)
    duracion = Column(String(100), nullable=False)

    receta = relationship("Receta", back_populates="detalles")