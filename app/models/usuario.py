from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    correo = Column(String(150), unique=True, index=True, nullable=False)
    contrasena_encriptada = Column(String(255), nullable=False)
    esta_activo = Column(Boolean, default=True)
    
    # Llave foránea hacia Roles
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    
    # Relación con la tabla Rol
    rol = relationship("Rol", back_populates="usuarios")

    # Relaciones de una sola vía (Uno a Uno) hacia los perfiles específicos
    medico = relationship("Medico", back_populates="usuario", uselist=False)
    paciente = relationship("Paciente", back_populates="usuario", uselist=False)