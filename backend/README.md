# CaféTrace SV

Plataforma geoespacial de trazabilidad agrícola para el sector cafetalero de **El Salvador**, orientada a facilitar la preparación técnica de pequeños y medianos productores frente al **Reglamento Europeo sobre Productos Libres de Deforestación (EUDR — Regulation (EU) 2023/1115)**.

> CaféTrace SV **no reemplaza** los sistemas oficiales del Instituto Salvadoreño del Café (ISC) ni el sistema central de la Comisión Europea. Es una capa de simplificación: transforma parcelas y cosechas en expedientes digitales, códigos QR de consulta pública y archivos GeoJSON estándar listos para exportar.

## Flujo central de trazabilidad

```
Organización → Usuario (Admin/Técnico/Productor) → Productor → Finca → Parcela (Polígono PostGIS) → Cosecha → Lote de café → QR / GeoJSON EUDR
```

---

## Stack tecnológico

| Capa | Tecnología |
| :--- | :--- |
| **API** | FastAPI (Python 3.11+) |
| **Validación** | Pydantic v2 |
| **Acceso a datos** | `asyncpg` — **sin ORM**, SQL directo y parametrizado |
| **Base de datos** | PostgreSQL 15+ con extensión **PostGIS** |
| **Autenticación** | JWT (`python-jose`) + Passlib (Argon2id) |
| **Frontend** | Fuera de alcance de este repo — cualquier cliente que consuma la API REST/JSON/GeoJSON |

**Decisión clave:** no se usa SQLAlchemy, GeoAlchemy2 ni ningún otro ORM. Todo el acceso a la base de datos se hace con consultas SQL escritas a mano en `app/db/queries/`, usando parámetros posicionales (`$1, $2, ...`) para prevenir inyección SQL.

---

## Requisitos previos

- Python 3.11+
- PostgreSQL 15+ con extensión `postgis` disponible
- pip

---

## Instalación y setup

```bash
# 1. Crear entorno virtual (desde la raíz del proyecto)
CafeTraceSV-Backend> python -m venv venv
CafeTraceSV-Backend> venv\Scripts\activate        # Windows
# source venv/bin/activate                         # Linux/Mac

# 2. Instalar dependencias
CafeTraceSV-Backend> cd backend
CafeTraceSV-Backend\backend> pip install -r requirements.txt

# 3. Verificar dependencias instaladas
CafeTraceSV-Backend\backend> pip list

# 4. Variables de entorno (.env en backend/)
DATABASE_URL=postgresql://usuario:password@localhost:5432/cafetrace_sv
JWT_SECRET_KEY=cambia-esto-por-un-secreto-real
JWT_ALGORITHM=HS256
```

## Levantar el servidor

```bash
# Opción A: uvicorn — ejecutar SIEMPRE desde backend/
CafeTraceSV-Backend\backend> uvicorn app.main:app --reload

# Opción B: CLI de FastAPI — ejecutar desde la raíz del proyecto
CafeTraceSV-Backend> fastapi dev backend/app/main.py
```

Ambos comandos levantan el servidor con recarga automática; solo cambia desde qué carpeta se ejecutan y la ruta al módulo. No mezclar los dos estilos en la documentación del equipo para evitar confusión.

Una vez arriba, la documentación interactiva queda disponible en:
```
http://127.0.0.1:8000/docs
```

---

## Estructura del proyecto (CONCEPTO NO FINAL)

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py                 # get_db, get_current_user, filtro por organización (RBAC)
│   │   └── v1/
│   │       ├── api.py              # Router principal, agrupa todos los endpoints
│   │       └── endpoints/
│   │           ├── auth.py         # Login, registro, JWT
│   │           ├── productores.py  # CRUD de productores
│   │           ├── fincas.py       # CRUD de fincas
│   │           ├── parcelas.py     # Parcelas, PostGIS, GeoJSON
│   │           ├── cosechas.py     # Cosechas y lotes
│   │           ├── trace.py        # Trazabilidad pública por QR
│   │           └── eudr.py         # Motor de preparación EUDR
│   ├── core/
│   │   ├── config.py                # Settings, CORS, DATABASE_URL
│   │   └── security.py              # Hasheo Argon2id y lógica JWT
│   ├── db/
│   │   ├── pool.py                  # Pool de conexiones asyncpg
│   │   └── queries/                 # SQL directo agrupado por entidad — NO son modelos ORM
│   │       ├── usuarios_sql.py
│   │       ├── organizaciones_sql.py
│   │       ├── productores_sql.py
│   │       ├── fincas_sql.py
│   │       ├── parcelas_sql.py
│   │       ├── cosechas_sql.py
│   │       └── lotes_cafe_sql.py
│   ├── schemas/                     # DTOs Pydantic (campos en español)
│   ├── services/                    # Lógica de negocio pura
│   │   ├── gis_service.py
│   │   └── eudr_service.py
│   └── main.py
├── db/
│   └── migraciones/                 # Scripts SQL versionados a mano (sin Alembic)
├── tests/
├── requirements.txt
└── README.md
```

**Regla de imports entre capas:** la dependencia siempre va hacia abajo — `endpoints → services → db/queries`. La capa `db/queries/` nunca importa nada de `api/`, para evitar imports circulares.

---

## Modelo de datos

Jerarquía completa: `organizaciones → usuarios → productores → fincas → parcelas → cosechas → lotes_cafe`.

### Tablas

| Tabla | Descripción |
| :--- | :--- |
| **organizaciones** | Cada "dueño" (empresa/cooperativa) usando la plataforma. Aísla los datos entre distintas organizaciones (multi-tenant). |
| **usuarios** | Cuentas de acceso al sistema. Todo usuario pertenece a una organización. Rol restringido por `CHECK` a `ADMIN`, `PRODUCTOR`, `TECNICO`. |
| **productores** | Extensión 1 a 1 de `usuarios` con rol `PRODUCTOR`: documento de identidad, teléfono, departamento, municipio. |
| **fincas** | Fincas de un productor. Un productor puede tener varias. |
| **parcelas** | Polígonos PostGIS (`GEOMETRY(POLYGON, 4326)`) de cada tablón de una finca. Se dibujan **una sola vez**; después solo se consultan. |
| **cosechas** | Registro recurrente por temporada, ligado a una parcela. |
| **lotes_cafe** | Lote comercial trazable, generado a partir de una cosecha. Incluye `qr_uuid` para el endpoint público de trazabilidad. |

### DDL

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

CREATE TABLE organizaciones (
    id_organizacion UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(150) NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE usuarios (
    id_usuario UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_organizacion UUID NOT NULL REFERENCES organizaciones(id_organizacion) ON DELETE CASCADE,
    correo VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(80) NOT NULL,
    nombres VARCHAR(50) NOT NULL,
    apellidos VARCHAR(50) NOT NULL,
    rol VARCHAR(30) NOT NULL DEFAULT 'PRODUCTOR'
        CHECK (rol IN ('ADMIN', 'PRODUCTOR', 'TECNICO')),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_usuarios_organizacion ON usuarios(id_organizacion);

CREATE TABLE productores (
    id_productor UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID UNIQUE NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    documento_identidad VARCHAR(50) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    departamento VARCHAR(50) NOT NULL,
    municipio VARCHAR(80) NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE fincas (
    id_finca UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_productor UUID NOT NULL REFERENCES productores(id_productor) ON DELETE CASCADE,
    nombre VARCHAR(120) NOT NULL,
    departamento VARCHAR(50) NOT NULL,
    municipio VARCHAR(80) NOT NULL,
    canton_caserio VARCHAR(120),
    altitud_msnm INTEGER,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE parcelas (
    id_parcela UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_finca UUID NOT NULL REFERENCES fincas(id_finca) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    variedad_cafe VARCHAR(60) NOT NULL,
    area_hectareas NUMERIC(10, 4) NOT NULL,
    geometria GEOMETRY(POLYGON, 4326) NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_parcelas_geometria ON parcelas USING GIST(geometria);

CREATE TABLE cosechas (
    id_cosecha UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_parcela UUID NOT NULL REFERENCES parcelas(id_parcela) ON DELETE CASCADE,
    fecha_cosecha DATE NOT NULL,
    peso_kg NUMERIC(10, 2) NOT NULL,
    porcentaje_humedad NUMERIC(5, 2),
    notas TEXT,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE lotes_cafe (
    id_lote UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_cosecha UUID NOT NULL REFERENCES cosechas(id_cosecha) ON DELETE CASCADE,
    codigo_lote VARCHAR(60) UNIQUE NOT NULL,
    qr_uuid UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    metodo_procesamiento VARCHAR(50) NOT NULL,
    puntaje_catacion NUMERIC(5, 2) NOT NULL,
    listo_exportacion BOOLEAN NOT NULL DEFAULT FALSE,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

> **Nota:** si exportas el esquema desde drawdb, `parcelas.geometria` puede aparecer como `BLOB` — es solo cómo drawdb representa tipos que no reconoce nativamente. En Postgres real debe quedar como `GEOMETRY(POLYGON, 4326)`, o las funciones espaciales (`ST_Area`, `ST_AsGeoJSON`) no van a funcionar.

---

## Endpoints principales

Todos bajo el prefijo `/api/v1`.

| Método | Ruta | Descripción | Auth |
| :--- | :--- | :--- | :--- |
| POST | `/auth/register` | Registro de usuario (queda ligado a una organización) | No |
| POST | `/auth/login` | Login, retorna `access_token` | No |
| GET | `/auth/me` | Datos del usuario autenticado | Sí |
| POST | `/productores` | Completa el perfil agrícola del productor | Sí |
| POST | `/fincas` | Crea una finca | Sí |
| GET | `/fincas` | Lista fincas de la organización del usuario | Sí |
| POST | `/parcelas` | Crea una parcela con su polígono GeoJSON | Sí |
| GET | `/parcelas/{id}/geojson` | Devuelve el `Feature` GeoJSON de una parcela | Sí |
| POST | `/cosechas` | Registra una cosecha sobre una parcela existente | Sí |
| POST | `/lotes_cafe` | Arma un lote comercial (genera `qr_uuid`) | Sí |
| GET | `/trace/{qr_uuid}` | Expediente público de trazabilidad | **No** |
| GET | `/eudr/fincas/{id}/estado` | Checklist de preparación EUDR de una finca | Sí |
| GET | `/eudr/fincas/{id}/exportar-geojson` | `FeatureCollection` exportable para el comprador/exportador | Sí |

---

## Reglas geoespaciales

- CRS obligatorio: **WGS84 (EPSG:4326)**.
- Coordenadas siempre `[longitud, latitud]` (nunca invertidas) — El Salvador: longitud `[-90.15, -87.68]`, latitud `[13.15, 14.45]`.
- Todo polígono debe estar cerrado (primer y último vértice idénticos), mínimo 4 coordenadas.
- El área en hectáreas se calcula en la propia consulta SQL:
  ```sql
  ST_Area(geometria::geography) / 10000.0
  ```

---

## Decisiones de diseño (resumen)

- **Sin ORM** — SQL directo con `asyncpg`, para máxima velocidad de desarrollo en el hackatón y control total sobre las consultas PostGIS.
- **Campos en español** en toda la base de datos y en los contratos de la API, para que el equipo trabaje con nombres naturales sin traducir mentalmente.
- **Sin `departamentos`/`municipios` como catálogo** — se dejan como texto libre por simplicidad; no se justificaba la normalización para el alcance del MVP.
- **Sin tabla `roles`** — un `CHECK` en `usuarios.rol` da la misma integridad sin overhead de joins.
- **`organizaciones` para multi-tenancy** — cada admin/dueño ve únicamente los datos de su propia organización. El filtro por `id_organizacion` debe aplicarse en **todo** endpoint de listado, siempre tomado del JWT del usuario autenticado, nunca de un parámetro que mande el cliente.
- **`qr_uuid` como UUID** — no decodificable, no adivinable, ideal para el endpoint público de trazabilidad. El QR codifica una URL, no los datos en sí; el expediente se arma en tiempo real al escanear.
- **Sin frontend definido en este repo** — cualquier cliente puede consumir la API vía REST/JSON/GeoJSON.

---

## Alcance del MVP (6 días)

No se agregan microservicios, brokers de mensajería (Kafka/RabbitMQ) ni bases NoSQL. Toda la persistencia se resuelve en PostgreSQL + PostGIS. Tampoco se modelan entidades de `compradoras`/`distribuidoras` como tablas separadas — si se necesita registrar esa info, se agregan campos simples y opcionales directamente en `lotes_cafe` (ej. `empresa_exportadora`, `empresa_procesadora`).