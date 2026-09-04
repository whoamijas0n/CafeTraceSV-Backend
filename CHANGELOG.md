# 📝 Changelog - CaféTrace SV Backend

Este documento detalla las modificaciones y depuraciones realizadas al proyecto para asegurar su correcta funcionalidad y conexión con el entorno de producción/pruebas.

## 🗓️ Fecha: 04 de Septiembre, 2026

### 🚀 Configuración de Infraestructura y Conectividad
- **Migración a PostGIS**: Se realizó el despliegue de una nueva instancia de base de datos **PostgreSQL 17 + PostGIS 3.5** en Railway para habilitar el soporte completo de consultas espaciales, topología y análisis geodésico.
- **Integración con Railway**: Se configuró el archivo `.env` con las credenciales oficiales de la base de datos PostgreSQL alojada en Railway.
- **Soporte Asíncrono**: Se habilitaron las dependencias `sqlalchemy` y `asyncpg` en el archivo `requirements.txt` para permitir conexiones asíncronas eficientes.
- **Validación de Base de Datos**: Se implementó una lógica de verificación real en el endpoint `/health` para comprobar la conectividad activa con la base de datos.

### 🛠️ Depuración y Optimización de la API (`main.py`)
- **Activación de Rutas Reales**: Se eliminaron todos los endpoints de "maqueta" (mocks) y se activó el `api_router` de la versión 1 (`/api/v1`), habilitando la lógica real de autenticación, productores, fincas y parcelas.
- **Resiliencia de PostGIS**: Se modificó la verificación de salud para que la API sea marcada como `healthy` siempre que la conexión a PostgreSQL sea exitosa, incluso si la extensión PostGIS no está instalada en el servidor (evitando bloqueos en el desarrollo inicial).
- **Mejora de Swagger**: Se organizaron los tags de la documentación automática para una mejor navegación en el panel de pruebas.

### 🧹 Limpieza y Estructuración del Proyecto
Se realizó una depuración profunda de la estructura de carpetas para eliminar archivos redundantes y ruido visual, dejando únicamente lo esencial para la ejecución:
- **Eliminación de Documentación Obsoleta**: Se borraron archivos `.md` y `.txt` redundantes en la raíz.
- **Eliminación de Infraestructura no Utilizada**:
    - Borrado de `Dockerfile` y `docker-compose.yml` (optimización para desarrollo local).
    - Borrado de `.env.example` y `requirements_full.txt`.
- **Simplificación de Directorios**: Se eliminó la carpeta `scripts/` y sus contenidos para mantener el enfoque en la aplicación (`app/`).

### 🏁 Estado Actual
- **Conectividad**: ✅ Exitosa (Railway).
- **API**: ✅ Operativa y accesible vía Swagger (`/docs`).
- **Entorno**: ✅ Optimizado y limpio.
