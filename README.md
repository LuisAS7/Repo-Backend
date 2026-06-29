# 🏥 ValSync - Backend API

*Read this in other languages: [Español](README-es.md)*

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Render](https://img.shields.io/badge/Render-%46E3B7.svg?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

ValSync backend, an MVP for comprehensive medical clinic management (HealthTech). This asynchronous RESTful API is built to handle the entire clinical workflow: from patient registration and double-booking prevention in medical scheduling, to vital signs recording (Triage) and clinical records (SOAP notes, Diagnoses, and Prescriptions).

It also serves as the core engine for the patient self-management portal (**ValCare**).

---

## 🌐 Live Deployment (Production)

The API is deployed and running on Render. You can explore and test the endpoints directly through the interactive Swagger UI interface:

* **🔗 Base URL:** `https://valsync-api.onrender.com`
* **📖 API Documentation (Swagger):** `https://valsync-api.onrender.com/docs`
* **🩺 Health Check:** `https://valsync-api.onrender.com/health`

---

## ✨ Key Features

* **Asynchronous Architecture:** Full `async/await` implementation using SQLAlchemy 2.0 and `asyncpg` for high-performance, non-blocking operations.
* **Security & Authentication (JWT):** Secure login system with JWT tokens, password hashing via `bcrypt`, and global route protection.
* **Role-Based Access Control (RBAC):** `RoleChecker` dependency that restricts access to specific endpoints based on user roles (`ADMIN`, `DOCTOR`, or `NURSE`).
* **Strict Clinical Workflow:** State machine for medical appointments (`SCHEDULED` ➡️ `WAITING` ➡️ `COMPLETED`), preventing logical bypasses (e.g., consultations cannot occur without prior triage).
* **Double-Booking Prevention:** Transactional logic to avoid scheduling conflicts between doctors and patients.
* **Soft Delete:** Logical deletion of records (Patients and Staff) using the `is_active` field and `PATCH` endpoints, preserving medical audit integrity.
* **Optimized Eager Loading:** Prevention of serialization errors (`MissingGreenlet`) through nested relational loading (`selectinload`).

---

## 🛠️ Tech Stack

* **Web Framework:** FastAPI
* **Database:** PostgreSQL (Hosted on Supabase)
* **ORM:** SQLAlchemy 2.0 (Async Engine)
* **DB Driver:** asyncpg
* **Migrations:** Alembic
* **Data Validation:** Pydantic v2
* **Security:** PyJWT, passlib, bcrypt
* **ASGI Server:** Uvicorn
* **Linter & Formatter:** Ruff, pre-commit

---

## 📂 Project Architecture

The project follows a domain-centric layered architecture to ensure scalability and separation of concerns:

```text
app/
 ├── api/          
 │   ├── deps.py          # Dependency injection (DB, JWT, RBAC)
 │   └── v1/routers/      # Controllers and Endpoints (Auth, Patients, Appointments, etc.)
 ├── core/         
 │   ├── config.py        # Environment validators and global settings
 │   ├── exceptions.py    # Custom HTTP exception handlers
 │   └── security.py      # Hashing logic and JWT generation
 ├── db/           
 │   └── database.py      # Async engine setup
 ├── models/       
 │   └── ...              # ORM Classes (PostgreSQL Tables)
 ├── schemas/      
 │   └── ...              # Pydantic Models (Request/Response Validation)
 ├── scripts/      
 │   ├── run_seed.py      # Database seeding orchestrator
 │   └── seeders/         # Scripts to populate catalogs and dummy data
 └── services/     
     └── ...              # Business Logic and CRUD transactions

```

---

## ⚙️ Local Setup & Deployment

Follow these steps to spin up the development environment on your local machine.

### 1. Prerequisites
* Python **3.13.4** (Recommended, pinned in `.python-version`).
* A PostgreSQL instance (local or Supabase).

### 2. Installation
Clone the repository and set up your virtual environment:

```bash
git clone [https://github.com/your-username/ValSync-Backend.git](https://github.com/your-username/ValSync-Backend.git)
cd ValSync-Backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables (.env)
Create a .env file in the root directory. Important note for Supabase: Use port 5432 (Direct Connection) for Alembic and port 6543 (Transaction Pooler) with ?pgbouncer=true for the async ORM.

```bash
# Database Configuration
DATABASE_URL="postgresql+asyncpg://user:password@host:6543/postgres?pgbouncer=true"
ALEMBIC_DATABASE_URL="postgresql://user:password@host:5432/postgres"

# Security Configurations
SECRET_KEY="your_super_secret_key_here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS (Frontend URLs)
CORS_ORIGINS="http://localhost:5173,http://localhost:3000,[https://your-frontend.vercel.app](https://your-frontend.netlify.app)"
```

### 4. Database & Seeders
Apply migrations to generate the tables and run the seeding script to populate base catalogs (Specialties, Allergies, etc.) and testing data.

```bash
# Apply schema to PostgreSQL
alembic upgrade head

# Insert mandatory catalogs and dummy data (Doctors, Patients, Appointments)
python -m app.scripts.run_seed --dummy
```
(Note: The --dummy command will generate an administrator user with the email admin@valsync.com).

### Start the Server
```bash
uvicorn app.main:app --reload
```
The API will be available at http://127.0.0.1:8000.
