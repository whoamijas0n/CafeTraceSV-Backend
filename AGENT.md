# AGENT.MD — Contexto de Desarrollo y Directrices del Sistema (Backend-First)

## 📌 1. Visión General del Proyecto: CaféTrace SV

**CaféTrace SV** es una plataforma tecnológica geoespacial y de trazabilidad agrícola diseñada para el sector cafetalero de **El Salvador**. Su objetivo principal es resolver la fragmentación documental de pequeños y medianos productores, facilitando la preparación técnica y el cumplimiento del **Reglamento Europeo sobre Productos Libres de Deforestación (EUDR - Regulation (EU) 2023/1115)**, que entra en vigor el **30 de diciembre de 2026**.

### 🎯 Propuesta de Valor y Enfoque Técnico
- **No busca duplicar ni reemplazar** los sistemas oficiales del Instituto Salvadoreño del Café (ISC) ni el sistema central de la Comisión Europea.
- **Capa de simplificación e interoperabilidad**: Transforma el trazado de parcelas y registros de cosechas en expedientes digitales estructurados, códigos QR de consulta pública y archivos **GeoJSON estándar (WGS84 / EPSG:4326)** listos para la exportación y procesos de debida diligencia (*Due Diligence*).
- **Flujo Central de Trazabilidad**:
  $$\text{Productor} \longrightarrow \text{Finca} \longrightarrow \text{Parcela (Polígono PostGIS)} \longrightarrow \text{Cosecha} \longrightarrow \text{Lote Comercial} \longrightarrow \text{QR / GeoJSON EUDR}$$

---

## 🛠️ 2. Arquitectura Global y Stack Tecnológico

La solución opera bajo una arquitectura desacoplada **API REST Asíncrona ↔ Base de Datos Espacial**, enfocada exclusivamente en el backend para maximizar el tiempo disponible en la hackatón. El consumo desde cualquier cliente (web, móvil o herramienta interna) se hace vía la API REST/JSON documentada; el frontend queda fuera del alcance de este documento y será decidido/implementado por separado según el tiempo disponible.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLIENTE (fuera de alcance de este doc)               │
│         Cualquier consumidor de la API REST / JSON / GeoJSON            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                             REST API / JSON / GeoJSON
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                       BACKEND CORE (DOMINIO DEL AGENTE)                 │
│      FastAPI (Python 3.11+) + Pydantic v2 + asyncpg (SQL directo)       │
│      Shapely (Motor GIS) + JWT/Argon2id (Seguridad)                     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                            PostGIS Spatial Queries
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                    BASE DE DATOS ESPACIAL & STORAGE                     │
│      PostgreSQL 15+ con Extensión PostGIS habilitada (vía Supabase)     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tabla de Tecnologías y Responsabilidades

| Capa | Tecnología | Rol en el Proyecto y Consideraciones de Compatibilidad |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI (Python 3.11+)** | Routing asíncrono, inyección de dependencias, endpoints OpenAPI/Swagger interactivos en `/docs`. |
| **Validación de Datos** | **Pydantic v2** | Serialización estricta, parseo de esquemas GeoJSON RFC 7946, validación de coordenadas y DTOs. |
| **Acceso a Datos** | **asyncpg (SQL directo, sin ORM)** | Consultas SQL parametrizadas escritas a mano (`$1, $2, ...`), sin capa de mapeo objeto-relacional. Soporte nativo de tipos geométricos de PostGIS vía funciones SQL (`ST_GeomFromGeoJSON`, `ST_AsGeoJSON`, `ST_Area`). |
| **Base de Datos** | **PostgreSQL + PostGIS (Supabase)** | Almacenamiento geoespacial, cálculo geodésico de áreas con `ST_Area(geography)`, exportación nativa `ST_AsGeoJSON`. |
| **Autenticación & Auth** | **JWT (python-jose) + Passlib (Argon2id / Bcrypt)** | Tokens Bearer en cabecera `Authorization: Bearer <token>`, roles: `ADMIN`, `PRODUCTOR`, `TECNICO`. |
| **Frontend** | *(fuera de alcance / a definir por el equipo)* | Consumirá los endpoints REST tal cual se documentan aquí. No se asume ningún framework específico. |

---

## 🗺️ 3. Reglas Geoespaciales Críticas (¡ATENCIÓN AGENTE!)

1. **Sistema de Referencia de Coordenadas (CRS)**:
   - Todo debe manejarse bajo **WGS84 (EPSG:4326)**.
   - En base de datos la columna es `GEOMETRY(POLYGON, 4326)`.
2. **Orden de Coordenadas (Estándar GeoJSON RFC 7946)**:
   - Las coordenadas deben ser estrictamente `[longitud, latitud]` (X, Y).
   - **NUNCA** invertir a `[latitud, longitud]`, ya que romperá el renderizado en cualquier visor de mapas y los cálculos de PostGIS.
   - El Salvador se ubica aproximadamente en: Longitud `[-90.15 a -87.68]`, Latitud `[13.15 a 14.45]`.
3. **Polígonos Válidos y Cerrados**:
   - El primer y el último vértice de un polígono deben ser **idénticos** (ej: 4 coordenadas representan un triángulo cerrado).
   - La superficie en hectáreas se calcula en PostGIS convirtiendo la geometría a geografía para considerar la curvatura terrestre:
     $$\text{area\_ha} = \frac{\text{ST\_Area}(\text{geometry}::\text{geography})}{10000.0}$$

---

## 🗄️ 4. Esquema Relacional y Modelo PostGIS (DDL — Campos en Español)

```sql
-- Habilitar extensión espacial y de UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- 1. USUARIOS Y AUTENTICACIÓN
CREATE TABLE usuarios (
    id_usuario UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correo VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(80) NOT NULL,
    nombres VARCHAR(50) NOT NULL,
    apellidos VARCHAR(50) NOT NULL,
    rol VARCHAR(30) NOT NULL DEFAULT 'PRODUCTOR', -- 'ADMIN', 'PRODUCTOR', 'TECNICO'
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- 2. PRODUCTORES
CREATE TABLE productores (
    id_productor UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_usuario UUID UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE,
    documento_identidad VARCHAR(50) NOT NULL, -- DUI / NIT / Pasaporte
    telefono VARCHAR(30),
    departamento VARCHAR(50) NOT NULL,   -- ej: Usulután, Santa Ana
    municipio VARCHAR(80) NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. FINCAS
CREATE TABLE fincas (
    id_finca UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    productor_id UUID NOT NULL REFERENCES productores(id) ON DELETE CASCADE,
    nombre VARCHAR(120) NOT NULL,
    departamento VARCHAR(50) NOT NULL,
    municipio VARCHAR(80) NOT NULL,
    canton_caserio VARCHAR(120),
    altitud_msnm INTEGER, -- Metros sobre el nivel del mar
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. PARCELAS (CON POLÍGONO POSTGIS)
CREATE TABLE parcelas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    finca_id UUID NOT NULL REFERENCES fincas(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    variedad_cafe VARCHAR(60) NOT NULL, -- Bourbon, Pacamara, Cuscatleco, Pacas, Geisha
    area_hectareas NUMERIC(10, 4) NOT NULL,
    geometria GEOMETRY(POLYGON, 4326) NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_parcelas_geometria ON parcelas USING GIST(geometria);

-- 5. COSECHAS
CREATE TABLE cosechas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcela_id UUID NOT NULL REFERENCES parcelas(id) ON DELETE CASCADE,
    fecha_cosecha DATE NOT NULL,
    peso_kg NUMERIC(10, 2) NOT NULL,
    porcentaje_humedad NUMERIC(5, 2),
    notas TEXT,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. LOTES DE CAFÉ Y TRAZABILIDAD
CREATE TABLE lotes_cafe (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cosecha_id UUID NOT NULL REFERENCES cosechas(id) ON DELETE CASCADE,
    codigo_lote VARCHAR(60) UNIQUE NOT NULL, -- ej: SV-USU-2026-LOT01
    qr_uuid UUID UNIQUE DEFAULT uuid_generate_v4(),
    metodo_procesamiento VARCHAR(50) NOT NULL, -- Lavado, Honey, Natural
    puntaje_catacion NUMERIC(5, 2),
    listo_exportacion BOOLEAN DEFAULT FALSE,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 📡 5. Especificación de Contratos API REST (Endpoints Clave)

Todos los endpoints responden bajo el prefijo `/api/v1`. Los cuerpos de petición/respuesta usan los mismos nombres de campo en español que la base de datos, para evitar una capa extra de mapeo/traducción.

### 5.1. Autenticación (`/api/v1/auth`)
* `POST /auth/register` → `{ correo, contrasena, nombre, apellido, rol }` → Retorna `UsuarioOut`.
* `POST /auth/login` → Formulario OAuth2 `username` (correo) + `password` (contraseña) → Retorna `{ access_token, token_type: "bearer" }`.
* `GET /auth/me` (Protegido) → Datos del usuario actual.

### 5.2. Fincas y Parcelas Espaciales (`/api/v1/fincas`, `/api/v1/parcelas`)
* `POST /fincas` → Crear finca asociada al productor autenticado.
* `GET /fincas` → Listar fincas del productor con conteo de parcelas y estado EUDR.
* `POST /parcelas` → **Creación Espacial de Parcela**:
  ```json
  // Cuerpo de la petición
  {
    "finca_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "nombre": "Tablón Los Cedros",
    "variedad_cafe": "Bourbon",
    "geojson": {
      "type": "Polygon",
      "coordinates": [
        [
          [-88.54321, 13.43210],
          [-88.54100, 13.43210],
          [-88.54100, 13.43000],
          [-88.54321, 13.43000],
          [-88.54321, 13.43210]
        ]
      ]
    }
  }
  ```
  *Lógica Backend (SQL directo, sin ORM)*:
  1. Validar polígono cerrado (a nivel de aplicación, con Shapely o validación manual).
  2. Guardar geometría en PostGIS con una consulta parametrizada usando `ST_GeomFromGeoJSON($n)`.
  3. Calcular automáticamente `area_hectareas` con `ST_Area(geometria::geography) / 10000` dentro de la misma consulta `INSERT ... RETURNING`.
  4. Retornar `ParcelaOut` con id, nombre, área calculada y GeoJSON formateado.

* `GET /parcelas/{id}/geojson` → Retorna un **Feature GeoJSON (RFC 7946)**:
  ```json
  {
    "type": "Feature",
    "properties": {
      "parcela_id": "c1f77d34-...",
      "finca_nombre": "Finca El Espino",
      "productor_nombre": "Jason Velásquez",
      "variedad": "Bourbon",
      "area_hectareas": 3.72
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [...]
    }
  }
  ```

### 5.3. Trazabilidad Pública y QR (`/api/v1/trazabilidad`)
* `GET /trazabilidad/{qr_uuid}` (**Público - Sin Autenticación**):
  - Retorna el expediente completo de trazabilidad:
    - Datos del Productor (Nombre, Municipio, Departamento).
    - Datos de la Finca (Nombre, Altitud).
    - Parcela de origen y polígono georreferenciado simplificado.
    - Datos de Cosecha (Fecha, Proceso, Variedad).
    - Código de Lote y sello digital de verificación.

### 5.4. Motor de Preparación EUDR (`/api/v1/eudr`)
* `GET /eudr/fincas/{finca_id}/estado` → Evalúa las siguientes reglas de negocio y devuelve:
  ```json
  {
    "finca_id": "9b1deb4d-...",
    "puntaje_preparacion": 85,
    "estado": "APTO_CON_OBSERVACIONES", // "COMPLETO", "INCOMPLETO", "CRITICO"
    "lista_verificacion": {
      "datos_productor_completos": true,
      "parcelas_georreferenciadas": true,
      "poligonos_validos": true,
      "cosechas_registradas": true,
      "tiene_cosecha_reciente": false
    },
    "requisitos_faltantes": [
      "Falta registrar fecha de cosecha para la parcela Tablón Los Cedros"
    ]
  }
  ```
* `GET /eudr/fincas/{finca_id}/exportar-geojson` → Descarga directa de archivo `FeatureCollection` con todos los metadatos exigidos por importadores europeos.

---

## 📁 6. Estructura de Directorios Recomendada para el Backend

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py                 # Dependencias (get_db, get_current_user, RBAC)
│   │   └── v1/
│   │       ├── api.py              # Enrutador principal de endpoints v1
│   │       └── endpoints/
│   │           ├── auth.py         # Login, Registro, JWT
│   │           ├── productores.py  # CRUD de Productores
│   │           ├── fincas.py       # CRUD de Fincas
│   │           ├── parcelas.py     # Parcelas, PostGIS, GeoJSON
│   │           ├── cosechas.py     # Cosechas y Lotes
│   │           ├── trazabilidad.py # Trazabilidad pública por QR
│   │           └── eudr.py         # Motor de preparación EUDR & exportador
│   ├── core/
│   │   ├── config.py               # Settings (Pydantic BaseSettings, CORS, DB_URL)
│   │   └── security.py             # Hasheo de contraseñas (Passlib) y JWT logic
│   ├── db/
│   │   ├── pool.py                 # Pool de conexiones asyncpg (crear/cerrar en startup/shutdown)
│   │   └── queries/                # SQL directo agrupado por entidad, sin ORM
│   │       ├── usuarios_sql.py
│   │       ├── productores_sql.py
│   │       ├── fincas_sql.py
│   │       ├── parcelas_sql.py
│   │       ├── cosechas_sql.py
│   │       └── lotes_cafe_sql.py
│   ├── schemas/                    # Modelos Pydantic (Request/Response DTOs, campos en español)
│   │   ├── usuario.py
│   │   ├── finca.py
│   │   ├── parcela.py              # Validación GeoJSON y coordenadas
│   │   ├── trazabilidad.py
│   │   └── eudr.py
│   ├── services/                   # Lógica de negocio pura
│   │   ├── gis_service.py          # Transformaciones geométricas y cálculos
│   │   └── eudr_service.py         # Evaluador de cumplimiento normativo
│   └── main.py                     # Instancia FastAPI, Middlewares, CORS
├── db/
│   └── migraciones/                # Scripts SQL versionados a mano (sin Alembic/ORM)
│       ├── 0001_init.sql
│       ├── 0002_indices_geoespaciales.sql
│       └── ...
├── tests/                          # Tests unitarios y de integración de endpoints
├── Dockerfile                      # Contenedor optimizado de producción
├── docker-compose.yml              # Configuración local con PostgreSQL/PostGIS
├── requirements.txt
└── README.md
```

---

## ⚙️ 7. Convenciones de Código y Buenas Prácticas Backend

1. **Gestión de CORS**:
   - Configurar `CORSMiddleware` en `main.py` con una lista de orígenes permitidos definida en `config.py` (variable de entorno), sin asumir un framework de frontend específico.
2. **Manejo de Geometrías con SQL directo (asyncpg)**:
   - Usar funciones SQL nativas (`ST_AsGeoJSON`, `ST_GeomFromGeoJSON`, `ST_Area`) directamente en las consultas, sin capa ORM intermedia.
   - En schemas de entrada, utilizar `geojson_pydantic` o schemas Pydantic con estructura `{ "type": "Polygon", "coordinates": List[List[List[float]]] }`.
   - Todas las consultas deben ser **parametrizadas** (`$1, $2, ...` con asyncpg) para evitar inyección SQL; nunca construir SQL por concatenación de strings.
3. **Manejo de Errores HTTP**:
   - Lanzar siempre `HTTPException(status_code=4xx, detail="Mensaje descriptivo")`.
   - Polígonos no cerrados o de menos de 4 vértices deben retornar `422 Unprocessable Entity` con explicación clara.
4. **Seed Data para El Salvador**:
   - Proveer un script `scripts/seed_data.py` (con SQL directo vía asyncpg) con datos de ejemplo realistas de zonas cafetaleras:
     - Departamentos: *Usulután, Santa Ana, Sonsonate, Ahuachapán*.
     - Variedades: *Bourbon, Pacamara, Cuscatleco, Pacas, Geisha*.
     - Rangos de altitud: *900 a 1600 msnm*.

---

## 🚀 8. Instrucciones de Operación para el LLM en Modo Agente

Cuando se te solicite implementar código para este backend:
1. **Mantén consistencia total en los nombres de campo**: todo en `snake_case` y en **español**, tanto en la base de datos como en los DTOs de Pydantic y las respuestas JSON de la API. No introduzcas nombres en inglés salvo términos técnicos sin traducción natural (ej. `id`, `qr_uuid`).
2. **No uses ORM**: todo el acceso a datos se hace con `asyncpg` y SQL escrito a mano, parametrizado. No introduzcas SQLAlchemy, GeoAlchemy2, Tortoise ni ningún otro ORM.
3. **Prioriza la robustez de las consultas PostGIS** antes de añadir librerías pesadas externas.
4. **Mantén el foco en el MVP de 6 días**: No añadas microservicios, brokers de mensajería (Kafka/RabbitMQ), bases de datos NoSQL, ni asumas un framework de frontend concreto. Toda la persistencia espacial y relacional se resuelve eficientemente en PostgreSQL + PostGIS con SQL directo.
5. **Asegura endpoints idempotentes y documentados** con sus respectivos tipos de retorno para que Swagger UI (`/docs`) sirva como documentación viva para el equipo.