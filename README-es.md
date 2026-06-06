# 🏥 ValSync - Backend API

*Leer en otros idiomas: [English](README.md)*

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Render](https://img.shields.io/badge/Render-%46E3B7.svg?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

Backend de **ValSync**, un MVP para la gestión integral de clínicas médicas (HealthTech). Esta API RESTful asíncrona está construida para manejar el flujo clínico completo: desde el registro de pacientes y prevención de colisiones en la agenda médica, hasta el registro de signos vitales (Triage) y expedientes clínicos (SOAP, Diagnósticos y Recetas). 

Además, sirve como motor para el portal de autogestión de pacientes (**ValCare**).

---

## 🌐 Despliegue en Vivo (Producción)

La API se encuentra desplegada y operando en Render. Puedes explorar y probar los endpoints directamente a través de la interfaz interactiva de Swagger UI:

* **🔗 Base URL:** `https://valsync-api.onrender.com`
* **📖 Documentación API (Swagger):** `https://valsync-api.onrender.com/docs`
* **🩺 Health Check:** `https://valsync-api.onrender.com/health`

---

## ✨ Características Principales

* **Arquitectura Asíncrona:** Implementación total de `async/await` usando SQLAlchemy 2.0 y `asyncpg` para un alto rendimiento sin bloqueos.
* **Seguridad y Autenticación (JWT):** Sistema de login seguro con tokens JWT, encriptación de contraseñas con `bcrypt`, y protección global de rutas.
* **Control de Acceso Basado en Roles (RBAC):** Dependencia `RoleChecker` que restringe el acceso a endpoints específicos dependiendo de si el usuario es `ADMIN`, `DOCTOR` o `NURSE`.
* **Flujo Clínico Estricto:** Máquina de estados para citas médicas (`SCHEDULED` ➡️ `WAITING` ➡️ `COMPLETED`), previniendo saltos lógicos (ej. no se puede dar consulta sin triage).
* **Prevención de Double-Booking:** Lógica transaccional para evitar cruces de horarios entre doctores y pacientes.
* **Soft Delete:** Eliminación lógica de registros (Pacientes y Staff) mediante el campo `is_active` y endpoints `PATCH`, preservando la integridad de la auditoría médica.
* **Eager Loading Optimizado:** Prevención de errores de serialización (`MissingGreenlet`) mediante cargas relacionales anidadas (`selectinload`).

---

## 🛠️ Stack Tecnológico

* **Framework Web:** FastAPI
* **Base de Datos:** PostgreSQL (Alojado en Supabase)
* **ORM:** SQLAlchemy 2.0 (Motor asíncrono)
* **Driver DB:** asyncpg
* **Migraciones:** Alembic
* **Validación de Datos:** Pydantic v2
* **Seguridad:** PyJWT, passlib, bcrypt
* **Servidor ASGI:** Uvicorn
* **Linter & Formatter:** Ruff, pre-commit

---

## 📂 Arquitectura del Proyecto

El proyecto sigue una arquitectura en capas centrada en el dominio para garantizar la escalabilidad y la separación de responsabilidades:

```text
app/
 ├── api/          
 │   ├── deps.py          # Inyección de dependencias (DB, JWT, RBAC)
 │   └── v1/routers/      # Controladores y Endpoints (Auth, Patients, Appointments, etc.)
 ├── core/         
 │   ├── config.py        # Validadores de entorno y variables globales
 │   ├── exceptions.py    # Manejadores de excepciones HTTP personalizados
 │   └── security.py      # Lógica de hashing y generación de JWT
 ├── db/           
 │   └── database.py      # Configuración del engine asíncrono
 ├── models/       
 │   └── ...              # Clases ORM (Tablas de PostgreSQL)
 ├── schemas/      
 │   └── ...              # Modelos Pydantic (Validación de Request/Response)
 ├── scripts/      
 │   ├── run_seed.py      # Orquestador de volcado de datos
 │   └── seeders/         # Scripts para poblar catálogos y datos dummy
 └── services/     
     └── ...              # Lógica de Negocio y transacciones CRUD

```

---

## ⚙️ Configuración y Despliegue Local
Sigue estos pasos para levantar el entorno de desarrollo en tu máquina local.

### 1. Prerrequisitos
- Python 3.13.4 (Recomendado, especificado en .python-version).

- Instancia de PostgreSQL (puedes usar el entorno local o Supabase).

### 2. Instalación
Clona el repositorio y configura tu entorno virtual:

```bash
git clone [https://github.com/your-username/ValSync-Backend.git](https://github.com/your-username/ValSync-Backend.git)
cd ValSync-Backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Variables de Entorno (.env)
Crea un archivo .env en la raíz del proyecto. Nota importante para Supabase: Usa el puerto 5432 (Conexión Directa) para Alembic y el puerto 6543 (Transaction Pooler) con ?pgbouncer=true para el ORM asíncrono.

```bash
# Database Configuration
DATABASE_URL="postgresql+asyncpg://usuario:password@host:6543/postgres?pgbouncer=true"
ALEMBIC_DATABASE_URL="postgresql://usuario:password@host:5432/postgres"

# Security Configurations
SECRET_KEY="tu_super_clave_secreta_aqui"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS (Frontend URLs)
CORS_ORIGINS="http://localhost:5173,http://localhost:3000,[https://tu-frontend.vercel.app](https://tu-frontend.netlify.app)"
```

### 4. Base de Datos y Seeders
Aplica las migraciones para generar las tablas y corre el script de seeding para poblar los catálogos base (Especialidades, Alergias, etc.) y datos de prueba.

```bash
# Aplicar esquema a PostgreSQL
alembic upgrade head

# Insertar catálogos obligatorios y datos dummy (Doctores, Pacientes, Citas)
python -m app.scripts.run_seed --dummy
```
(Nota: El comando --dummy generará un usuario administrador con correo admin@valsync.com).

### 5. Iniciar el Servidor
```bash
uvicorn app.main:app --reload
```
La API estará disponible en http://127.0.0.1:8000.
