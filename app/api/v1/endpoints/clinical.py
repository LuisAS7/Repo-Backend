from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.clinical import EspecialidadRespuesta, EspecialidadCrear
from app.crud import clinical as crud_clinical
# Nota: Aquí simulamos la función get_db que irá en core/database más adelante
from app.db.session import get_db 

router = APIRouter(
    prefix="/clinica",
    tags=["Módulo Clínico"]
)

@router.post("/especialidades", response_model=EspecialidadRespuesta)
def guardar_especialidad(especialidad: EspecialidadCrear, db: Session = Depends(get_db)):
    return crud_clinical.crear_especialidad(db=db, especialidad=especialidad)

@router.get("/especialidades", response_model=List[EspecialidadRespuesta])
def listar_especialidades(db: Session = Depends(get_db)):
    return crud_clinical.obtener_especialidades(db=db)