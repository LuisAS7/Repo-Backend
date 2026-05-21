from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, Date, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# ==========================================
# 1. ENTIDAD: ESPECIALIDADES
# ==========================================
class Especialidad(Base):
    __tablename__ = "especialidades"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    esta_activo = Column(Boolean, default=True)

    # Relación: Una especialidad tiene muchos médicos
    medicos = relationship("Medico", back_populates="especialidad")


# ==========================================
# 2. ENTIDAD: MÉDICOS
# ==========================================
class Medico(Base):
    __tablename__ = "medicos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), unique=True, nullable=False)
    especialidad_id = Column(Integer, ForeignKey("especialidades.id", ondelete="RESTRICT"), nullable=False)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=True)
    numero_colegiatura = Column(String(50), unique=True, nullable=False)
    url_foto_perfil = Column(String(255), nullable=True)  # La foto para ValCare

    # Relaciones
    usuario = relationship("Usuario", back_populates="medico")
    especialidad = relationship("Especialidad", back_populates="medicos")
    horarios = relationship("HorarioMedico", back_populates="medico", cascade="all, delete-orphan")


# ==========================================
# 3. ENTIDAD: HORARIOS MÉDICOS
# ==========================================
class HorarioMedico(Base):
    __tablename__ = "horarios_medicos"

    id = Column(Integer, primary_key=True, index=True)
    medico_id = Column(Integer, ForeignKey("medicos.id", ondelete="CASCADE"), nullable=False)
    dia_semana = Column(Integer, nullable=False)  # 0=Lunes, 6=Domingo
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    duracion_cita = Column(Integer, nullable=False, default=30)  # En minutos

    # Relación
    medico = relationship("Medico", back_populates="horarios")


# ==========================================
# 4. ENTIDAD: PACIENTES
# ==========================================
class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), unique=True, nullable=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    dni_o_pasaporte = Column(String(20), unique=True, index=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    tipo_sangre = Column(String(5), nullable=True)

    # Relación
    usuario = relationship("Usuario", back_populates="paciente")