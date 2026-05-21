from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# Tabla intermedia Muchos a Muchos entre Roles y Permisos
roles_permisos = Table(
    "roles_permisos",
    Base.metadata,
    Column("rol_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", Integer, ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True)
)

class Permiso(Base):
    __tablename__ = "permisos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, index=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    # Relación inversa con Roles
    roles = relationship("Rol", secondary=roles_permisos, back_populates="permisos")


class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, index=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    # Relaciones
    permisos = relationship("Permiso", secondary=roles_permisos, back_populates="roles")
    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    correo = Column(String(150), unique=True, index=True, nullable=False)
    contrasena_encriptada = Column(String(255), nullable=False)
    esta_activo = Column(Boolean, default=True)
    
    # Llave foránea hacia Roles
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    
    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")
    medico = relationship("Medico", back_populates="usuario", uselist=False)
    paciente = relationship("Paciente", back_populates="usuario", uselist=False)