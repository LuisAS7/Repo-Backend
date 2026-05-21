# 🩺 Ecosistema Clínico: ValSync & ValCare

¡Bienvenido al repositorio central del Backend! Este proyecto es una API REST robusta, escalable y asíncrona diseñada para dar soporte a dos plataformas web integradas que modernizan la atención médica:

1. **ValSync:** Panel de gestión interna para la clínica. Permite a administradores, recepcionistas y médicos gestionar el flujo de atención, módulos de usuario, roles, permisos y el registro de historias clínicas en tiempo real.
2. **ValCare:** Portal web de cara al paciente. Permite el auto-registro, exploración dinámica de médicos por especialidad, visualización de horarios disponibles, reserva de citas y consulta de recetas médicas.

---

## 🛠️ Stack Tecnológico (¿Por qué lo elegimos?)

Para garantizar un rendimiento óptimo y una alta velocidad de desarrollo, implementamos el siguiente stack:

* **Python 3.10+**: Elegido por su legibilidad, madurez y excelente ecosistema para el manejo de datos y lógica de negocio.
* **FastAPI**: Un framework moderno, de alto rendimiento y asíncrono (gracias a `asyncio` y `Uvicorn`). Genera automáticamente documentación interactiva y maneja validaciones nativas de datos.
* **SQLAlchemy**: El ORM (Object-Relational Mapping) líder en Python. Nos permite interactuar con la base de datos usando programación orientada a objetos, aislando la lógica de consultas SQL y evitando inyecciones de código malicioso.
* **Pydantic**: Utilizado para la validación de esquemas y parseo de datos entrantes y salientes de la API, asegurando que la información clínica cumpla con el formato estricto requerido.
* **React (Frontend Relacionado)**: Se conecta nativamente con esta API consumiendo endpoints JSON, permitiendo una experiencia de usuario fluida y reactiva en ambas aplicaciones.

---

## 📂 Arquitectura Modular del Proyecto

El backend sigue un patrón de diseño limpio y desacoplado, organizando el código por responsabilidades:

```text
Repo-Backend/
├── app/
│   ├── api/            # Capa de controladores (Rutas y Endpoints de la API)
│   │   └── v1/
│   │       └── endpoints/  -> Rutas separadas (auth.py, clinical.py, etc.)
│   ├── core/           # Seguridad global (JWT, hashing de contraseñas), variables de entorno y RBAC
│   ├── crud/           # Operaciones directas a la Base de Datos (Create, Read, Update, Delete)
│   ├── db/             # Configuración de la conexión y sesión del ORM (SQLAlchemy Base Class)
│   ├── models/         # Entidades de la base de datos (Estructuras de las tablas físicas)
│   └── schemas/        # Modelos de validación de datos y DTOs (Pydantic)
├── venv/               # Entorno virtual de Python (Excluido de Git mediante .gitignore)
├── README.md           # Documentación técnica del proyecto
└── requirements.txt    # Manifiesto de dependencias instaladas y sus versiones

python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt 

