from sqlalchemy.orm import Session
from app.models.clinical import Especialidad
from app.schemas.clinical import EspecialidadCrear

# Función para buscar una especialidad por su ID
def obtener_especialidad(db: Session, especialidad_id: int):
    return db.query(Especialidad).filter(Especialidad.id == especialidad_id).first()

# Función para listar todas las especialidades activas
def obtener_especialidades(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Especialidad).filter(Especialidad.esta_activo == True).offset(skip).limit(limit).all()

# Función para guardar una nueva especialidad
def crear_especialidad(db: Session, especialidad: EspecialidadCrear):
    db_especialidad = Especialidad(
        nombre=especialidad.nombre,
        descripcion=especialidad.descripcion,
        esta_activos=especialidad.esta_activo
    )
    db.add(db_especialidad)
    db.commit()
    db.refresh(db_especialidad)
    return db_especialidad