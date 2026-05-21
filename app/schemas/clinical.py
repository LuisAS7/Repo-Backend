from pydantic import BaseModel
from typing import Optional

# Esquema base con los campos comunes
class EspecialidadBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    esta_activo: Optional[bool] = True

# Datos necesarios para CREAR una especialidad (lo que viene del Frontend)
class EspecialidadCrear(EspecialidadBase):
    pass  # Pide lo mismo que la base por ahora

# Estructura de los datos que la API DEVUELVE al Frontend (incluye el ID de la BD)
class EspecialidadRespuesta(EspecialidadBase):
    id: int

    class Config:
        from_attributes = True  # Permite a Pydantic leer modelos de SQLAlchemy