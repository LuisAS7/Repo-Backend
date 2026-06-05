# 🏥 ValSync - Backend API

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-blue.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)

Backend de ValSync, un MVP para la gestión integral de clínicas médicas (HealthTech). Esta API RESTful está construida para manejar el flujo de pacientes, agendas médicas, triages y expedientes clínicos, interconectando al personal de la clínica y al portal de autogestión de pacientes (ValCare).

## 🚀 Tecnologías Principales

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Asíncrono y de alto rendimiento)
* **Base de Datos:** PostgreSQL alojado en [Supabase](https://supabase.com/)
* **ORM:** SQLAlchemy 2.0 + Asyncpg (Conexiones asíncronas)
* **Migraciones:** Alembic
* **Validación de Datos:** Pydantic

## 📂 Arquitectura del Proyecto

El proyecto sigue una arquitectura en capas para garantizar la escalabilidad y separación de responsabilidades:

```text
app/
 ├── api/          # Controladores y Endpoints de FastAPI (Rutas)
 ├── core/         # Configuraciones globales, JWT y Seguridad
 ├── db/           # Configuración de la sesión y conexión a PostgreSQL
 ├── models/       # Modelos SQLAlchemy (Mapeo de la Base de Datos)
 ├── schemas/      # Modelos Pydantic (Validación de JSON de entrada/salida)
 └── services/     # Lógica de Negocio y operaciones CRUD