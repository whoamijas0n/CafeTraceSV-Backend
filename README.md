# ☕ CaféTrace SV — Backend

Bienvenido al núcleo de interoperabilidad y trazabilidad geoespacial de **CaféTrace SV**. Este backend ha sido diseñado para gestionar la trazabilidad agrícola del café salvadoreño, asegurando el cumplimiento de normativas internacionales como el **EUDR (Reglamento UE 2023/1115)** sobre productos libres de deforestación.

## 🚀 Características Principales

### 🗺️ Análisis Geoespacial Avanzado
- **Soporte PostGIS**: Integración completa con PostgreSQL 17 y PostGIS 3.5 para el manejo de geometrías complejas.
- **Cálculo Geodésico**: Medición precisa de áreas de parcelas utilizando el elipsoide terrestre para evitar distorsiones cartográficas.
- **Estándar GeoJSON**: Exportación de datos en formato GeoJSON RFC 7946, optimizado para visualización en MapLibre GL y Leaflet.
- **Validación Territorial**: Verificación de que las coordenadas de las fincas se encuentren dentro de los límites geográficos de El Salvador.

### 🔐 Seguridad y Autenticación
- **OAuth2 con JWT**: Implementación de tokens Bearer para acceso seguro a los endpoints.
- **Gestión de Roles**: Control de acceso para productores, administradores y entes reguladores.
- **CORS Configurable**: Soporte para integración segura con frontends modernos (Next.js/React).

### ⚡ Rendimiento y Escalabilidad
- **Asincronismo Total**: Construido con **FastAPI** y **SQLAlchemy 2.0 (Async)** para manejar múltiples peticiones concurrentes sin bloquear el hilo principal.
- **Conexiones Eficientes**: Uso de `asyncpg` para una comunicación optimizada con la base de datos.
- **Documentación Automática**: Panel de pruebas interactivo vía Swagger y ReDoc.

## 🛠️ Stack Tecnológico
- **Lenguaje**: Python 3.10+
- **Framework**: FastAPI
- **Base de Datos**: PostgreSQL 17 + PostGIS 3.5
- **ORM**: SQLAlchemy 2.0 (Async)
- **Validación**: Pydantic v2
- **Autenticación**: PyJWT / Passlib

---

## 📦 Guía de Instalación Paso a Paso

Sigue estas instrucciones para desplegar el backend en una nueva máquina.

### 1. Requisitos Previos
Asegúrate de tener instalado:
- **Python 3.10 o superior**
- **PostgreSQL 17** con la extensión **PostGIS 3.5** instalada y activa.
- **Git**

### 2. Clonar el Repositorio
```bash
git clone https://github.com/whoamijas0n/CafeTraceSV-Backend.git
cd CafeTraceSV-Backend
```

### 3. Configurar el Entorno Virtual
Es fundamental usar un entorno virtual para evitar conflictos de dependencias.

**En Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**En Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalación de Dependencias
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 5. Configuración de Variables de Entorno
El sistema utiliza un archivo `.env` para gestionar credenciales sensibles.

1. Ve a la carpeta `backend/`.
2. Copia el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```
3. Abre el archivo `.env` y completa los datos de tu base de datos PostgreSQL/PostGIS y la `SECRET_KEY` para los tokens JWT.

### 6. Inicialización de la Base de Datos
Ejecuta el script de inicialización para crear las tablas y habilitar la extensión PostGIS:
```bash
python backend/init_db.py
```

### 7. Ejecutar el Servidor
Inicia la aplicación utilizando `uvicorn`:
```bash
uvicorn backend.app.main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

---

## 📖 Documentación de la API

Una vez que el servidor esté corriendo, puedes acceder a la documentación interactiva para probar los endpoints:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) (Recomendado para pruebas rápidas)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc) (Ideal para lectura técnica)

## 📂 Estructura del Proyecto
```text
backend/
├── app/
│   ├── api/        # Rutas y controladores (Endpoints)
│   ├── core/       # Configuración global y seguridad
│   ├── db/         # Conexiones y sesiones de base de datos
│   ├── models/     # Modelos de SQLAlchemy (Esquema DB)
│   ├── schemas/    # Modelos de Pydantic (Validación de datos)
│   └── services/   # Lógica de negocio y cálculos GIS
├── .env            # Variables secretas (Ignorado por Git)
├── .env.example    # Plantilla de configuración
└── requirements.txt # Dependencias del proyecto
```
