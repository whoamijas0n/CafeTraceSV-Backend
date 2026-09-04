# CaféTrace SV — Changelog y Funcionamiento General

## Setup del entorno

```bash
# Crear entorno virtual
CafeTraceSV-Backend> python -m venv venv
CafeTraceSV-Backend> venv\Scripts\activate

# Instalar dependencias
CafeTraceSV-Backend> cd backend
CafeTraceSV-Backend\backend> pip install -r requirements.txt

# Verificación de dependencias del entorno
CafeTraceSV-Backend\backend> pip list

# Levantar el servidor (SIEMPRE desde la carpeta backend/, nunca desde app/)
CafeTraceSV-Backend\backend> uvicorn app.main:app --reload

# Alternativa: modo desarrollo con el CLI de FastAPI (equivalente, con recarga automática)
# Esta se ejecuta desde la raíz del proyecto (CafeTraceSV-Backend/), no desde backend/
CafeTraceSV-Backend> fastapi dev backend/app/main.py
```

> Nota: `uvicorn app.main:app --reload` y `fastapi dev backend/app/main.py` hacen lo mismo (levantan el servidor con recarga en caliente); la diferencia es solo desde qué carpeta los ejecutas y la ruta que le pasas a cada uno. Usa el que le quede más cómodo al equipo, pero no mezclen ambos estilos de ruta en la documentación para no confundir a alguien que copie el comando equivocado.

---

## Changelog de decisiones de arquitectura

### v0.1 — Diseño inicial
- Backend con FastAPI + SQLAlchemy 2.0 + GeoAlchemy2 (ORM), frontend planeado en Next.js 14.
- Campos de base de datos en inglés (`users`, `farms`, `plots`...).

### v0.2 — Sin ORM
- Se elimina SQLAlchemy/GeoAlchemy2. Todo el acceso a datos pasa a **SQL directo con `asyncpg`**, consultas parametrizadas (`$1, $2...`).
- Se elimina Alembic (dependía del ORM); las migraciones ahora son archivos `.sql` versionados a mano en `db/migraciones/`.

### v0.3 — Campos en español
- Todas las tablas y columnas se traducen: `usuarios`, `productores`, `fincas`, `parcelas`, `cosechas`, `lotes_cafe`.
- Los contratos de la API (JSON de request/response, nombres de rutas) se alinean también en español para no tener una capa de traducción intermedia.

### v0.4 — Sin Next.js
- Se remueve toda mención a un frontend específico. El backend queda como API REST pura, consumible por cualquier cliente.

### v0.5 — IDs en UUID + catálogo geográfico (evaluado y revertido)
- Se evaluó `departamentos` + `municipios` como catálogo normalizado.
- **Decisión final: no se usa.** Se mantiene `departamento`/`municipio` como texto libre (`VARCHAR`) en `productores` y `fincas`, por simplicidad para el MVP de 6 días.

### v0.6 — CHECK de roles (en vez de tabla `roles`)
- Se evaluó crear una tabla `roles` separada.
- **Decisión final: no se usa.** Se agrega un `CHECK (rol IN ('ADMIN', 'PRODUCTOR', 'TECNICO'))` directamente en `usuarios.rol` — misma integridad, sin `JOIN` extra.

### v0.7 — Multi-tenancy con tabla `organizaciones`
- Problema detectado: dos "dueños" distintos (cada uno con sus propios técnicos y productores) no debían ver los datos del otro.
- Se evaluó una columna auto-referenciada `id_admin` en `usuarios` → descartada por limitada (no modela la organización como entidad, no escala).
- **Decisión final:** tabla `organizaciones` real. Todo `usuario` (sin importar el rol) pertenece a una `organizacion` vía `id_organizacion`. Aislamiento de datos = filtrar siempre por `id_organizacion` del usuario autenticado (JWT).

### v0.8 — QR de trazabilidad
- Se confirma `qr_uuid` como `UUID` (no decodificable, no adivinable) para el endpoint público `GET /trace/{qr_uuid}`.
- El QR impreso codifica una URL (`https://tudominio.com/trace/{qr_uuid}`), no los datos en sí — el expediente se arma en tiempo real consultando la base de datos al escanear.

### Nota importante sobre `parcelas.geometria`
El documento de drawdb muestra el campo `geometria` como tipo `BLOB` — esto es solo una limitación de cómo drawdb representa tipos que no reconoce nativamente (PostGIS no es un tipo estándar SQL). **En la base de datos real, esta columna debe crearse como:**
```sql
geometria GEOMETRY(POLYGON, 4326) NOT NULL
```
No como `BLOB`. Si generan el `CREATE TABLE` a partir de la exportación de drawdb tal cual, hay que corregir manualmente esta línea o el polígono no funcionará con las funciones espaciales (`ST_Area`, `ST_AsGeoJSON`, etc.).

---

## Cómo funciona la app hoy (flujo end-to-end)

### 1. Alta de una organización y su primer admin
Esto se hace una sola vez, cuando un nuevo "dueño" (tú, o tu amigo) empieza a usar el sistema.

```sql
INSERT INTO organizaciones (id_organizacion, nombre)
VALUES (uuid_generate_v4(), 'Finca El Espino S.A.')
RETURNING id_organizacion;
```

```
POST /api/v1/auth/register
{
  "id_organizacion": "9b1deb4d-...",
  "correo": "admin@elespino.com",
  "password": "AdminClaveSegura789!",
  "nombres": "María",
  "apellidos": "Hernández",
  "rol": "ADMIN"
}
```

### 2. El admin crea a su técnico y a su productor
Ambos quedan ligados a la **misma** `id_organizacion` del admin que los registra (esto va resuelto en el backend, no lo manda el cliente — se toma del token del admin autenticado).

```
POST /api/v1/auth/register
{
  "correo": "tecnico.paco@elespino.com",
  "password": "OtraClaveSegura456!",
  "nombres": "Paco",
  "apellidos": "Martínez",
  "rol": "TECNICO"
}
```

```
POST /api/v1/auth/register
{
  "correo": "jason.velasquez@example.com",
  "password": "MiClaveSegura123!",
  "nombres": "Jason",
  "apellidos": "Velásquez",
  "rol": "PRODUCTOR"
}
```

### 3. El productor completa su perfil agrícola
Registrarse como `PRODUCTOR` no crea automáticamente su fila en `productores` — es un segundo paso, porque necesita datos adicionales.

```
POST /api/v1/productores
{
  "documento_identidad": "01234567-8",
  "telefono": "7890-1234",
  "departamento": "Usulután",
  "municipio": "Usulután"
}
```

Guardado real (SQL directo, sin ORM):
```sql
INSERT INTO productores (id_productor, id_usuario, documento_identidad, telefono, departamento, municipio)
VALUES (uuid_generate_v4(), $1, $2, $3, $4, $5)
RETURNING id_productor;
```

### 4. El productor registra su finca (una sola vez)
```
POST /api/v1/fincas
{
  "nombre": "Finca El Espino",
  "departamento": "Usulután",
  "municipio": "Usulután",
  "canton_caserio": null,
  "altitud_msnm": 1200
}
```

### 5. El productor dibuja y guarda su parcela (una sola vez, dato estructural)
```
POST /api/v1/parcelas
{
  "id_finca": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "nombre": "Tablón Los Cedros",
  "variedad_cafe": "Bourbon",
  "geojson": {
    "type": "Polygon",
    "coordinates": [[
      [-88.54321, 13.43210],
      [-88.54100, 13.43210],
      [-88.54100, 13.43000],
      [-88.54321, 13.43000],
      [-88.54321, 13.43210]
    ]]
  }
}
```

Guardado real:
```sql
INSERT INTO parcelas (id_parcela, id_finca, nombre, variedad_cafe, area_hectareas, geometria)
VALUES (
    uuid_generate_v4(),
    $1,
    $2,
    $3,
    ST_Area(ST_GeomFromGeoJSON($4)::geography) / 10000.0,
    ST_GeomFromGeoJSON($4)
)
RETURNING id_parcela, area_hectareas, ST_AsGeoJSON(geometria) AS geojson;
```

A partir de aquí, **cada vez que se consulte esta finca, la parcela ya está guardada** — nadie vuelve a dibujarla, solo se lee:
```sql
SELECT id_parcela, nombre, variedad_cafe, area_hectareas, ST_AsGeoJSON(geometria) AS geojson
FROM parcelas
WHERE id_finca = $1;
```

### 6. Cada temporada: solo se registra la cosecha (dato recurrente)
```
POST /api/v1/cosechas
{
  "id_parcela": "c1f77d34-...",
  "fecha_cosecha": "2026-11-15",
  "peso_kg": 450.5,
  "notas": "Corte de temporada"
}
```

### 7. Se arma el lote de café para exportación
```
POST /api/v1/lotes_cafe
{
  "id_cosecha": "d2f88e45-...",
  "codigo_lote": "SV-USU-2026-LOT01",
  "metodo_procesamiento": "Lavado",
  "puntaje_catacion": 86.5
}
```

Esto genera automáticamente el `qr_uuid` (`uuid_generate_v4()` por default en la tabla).

### 8. Trazabilidad pública vía QR
El QR impreso codifica: `https://tudominio.com/trace/{qr_uuid}`.

```
GET /api/v1/trace/{qr_uuid}   (público, sin autenticación)
```

Devuelve el expediente completo armado en el momento (productor, finca, parcela con su GeoJSON, cosecha, lote) — no hay nada "guardado" en el QR mismo, solo se usa como llave de búsqueda.

### 9. Aislamiento entre organizaciones (multi-tenant)
Cuando el admin de "Finca El Espino" pide sus fincas, el backend **siempre** filtra por su propia `id_organizacion` (sacada del JWT, nunca de un parámetro que mande el cliente):

```sql
SELECT f.id_finca, f.nombre, p.documento_identidad, u.nombres, u.apellidos
FROM fincas f
JOIN productores p ON p.id_productor = f.id_productor
JOIN usuarios u ON u.id_usuario = p.id_usuario
WHERE u.id_organizacion = $1;
```

Así, aunque tu amigo tenga su propia organización con sus propios productores y fincas en la misma base de datos, cada quien solo ve lo suyo.

---

## Resumen de qué se guarda una sola vez vs. qué se repite

| Dato | ¿Cuándo se crea? | ¿Se repite? |
|---|---|---|
| `organizaciones` | Al dar de alta un nuevo dueño | No |
| `usuarios` | Al registrar cada persona (admin, técnico, productor) | Una vez por persona |
| `productores` | Al completar el perfil agrícola | Una vez por productor |
| `fincas` | Al registrar cada finca | Una vez por finca |
| `parcelas` (con `geometria`) | Al dibujar el polígono | Una vez por parcela — **nunca se vuelve a dibujar** |
| `cosechas` | Cada corte/temporada | Sí, recurrente |
| `lotes_cafe` (con `qr_uuid`) | Al armar un lote para exportación | Sí, uno por lote comercial |


## Avances esperados para viernes

- conexion bd con python
- api lista para pruebas
- inicio de sesion con jwt
- maqueta inicial lista
- funcionalidades maplibre en proceso


## Avances esperados para sabado

- api lista para rest completo
- conexion con el backend api
- desarollo frontend crud
- integracion de deforestacion en capa
- Integracion de qr (generador de carga segun la ley europea)


## Avances esperados para el domingo 
- Testing y pendtesting 
- Integraciones de seguridad
- Puluir lo mas posible para la entrega