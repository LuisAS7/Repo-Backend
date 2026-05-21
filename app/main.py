from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Ecosistema Clínico API (ValSync & ValCare)",
    description="Backend centralizado para la gestión interna de la clínica (ValSync) y el portal de pacientes (ValCare).",
    version="1.0.0"
)

# Orígenes permitidos (aquí irán los puertos de React de ambas apps)
origins = [
    "http://localhost:3000",  # Frontend de ValSync (ejemplo)
    "http://localhost:5173",  # Frontend de ValCare (ejemplo)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API Global de ValSync & ValCare"}