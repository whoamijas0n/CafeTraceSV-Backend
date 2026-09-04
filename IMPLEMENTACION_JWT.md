# Documento de Implementacion e Integracion de Autenticacion JWT - CafeTrace SV

Este documento detalla la implementacion, integracion y validacion de la autenticacion basada en JSON Web Tokens (JWT) en el backend de CafeTrace SV. Describe los componentes actualizados, la arquitectura de seguridad, los resultados de pruebas y la hoja de ruta para las siguientes etapas del proyecto.

---

## 1. Contexto y Objetivos Tecnicos

CafeTrace SV requiere un mecanismo de seguridad y gestion de identidades solido y desacoplado, compatible con una arquitectura asincrona moderna (Python 3.11+, FastAPI, SQLAlchemy 2.0 Async, Pydantic v2 y PostgreSQL/PostGIS).

Los objetivos principales de esta intervencion fueron:
- Habilitar y conectar de forma definitiva las rutas modulares de autenticacion dentro del flujo de la aplicacion FastAPI.
- Remover rutas provisionales o de prueba (mock) del archivo central `main.py`.
- Garantizar el cumplimiento del estandar OAuth2 Password Bearer para que la documentacion interactiva de Swagger UI (`/docs`) permita autorizar peticiones directamente desde la interfaz.
- Asegurar que los tokens contengan los claims minimos requeridos por la plataforma (`sub`, `iat`, `exp`, `email`, `role` y `full_name`).
- Proteger los endpoints de negocio (productores, fincas, parcelas) sin alterar la logica geoespacial existente.

---

## 2. Componentes Modificados y Cambios Implementados

### 2.1. Archivo Central: `backend/app/main.py`
- Limpieza de rutas provisionales: Se removieron todos los endpoints de prueba hardcodeados (`/api/auth/*`, `/api/producers/*`, `/api/farms/*`, `/api/plots/*`) que devolvian respuestas estaticas.
- Integracion del enrutador modular: Se importo e incluyo `api_router` bajo el prefijo oficial establecido en la configuracion (`/api/v1`), consolidando los modulos de autenticacion, productores, fincas y parcelas.
- Correccion de importaciones de paquete: Se estandarizaron las importaciones absolutas referenciando la raiz `app.` (`from app.api.v1.api import api_router`, `from app.core.config import settings`, `from app.db.session import async_engine`).
- Endpoint de monitoreo (`/health`): Se configuro una comprobacion de salud del servicio que evalua la conexion asincrona a PostgreSQL y reporta la version de PostGIS disponible sin interrumpir el servicio en caso de indisponibilidad temporal de la base de datos.
- Endpoint raiz (`/`): Se conservo el endpoint de bienvenida con su respectiva etiqueta OpenAPI.

### 2.2. Modulo Criptografico y Tokens: `backend/app/core/security.py`
- Generacion de tokens (`create_access_token`): Se adapto la funcion para permitir la incorporacion explicita de los claims obligatorios:
  - `sub`: Identificador unico del usuario (UUID convertido a cadena).
  - `iat`: Timestamp UTC de emision del token.
  - `exp`: Timestamp UTC de expiracion del token.
  - `email`: Correo electronico institucional o personal del usuario.
  - `role`: Rol del usuario en el sistema (`ADMIN`, `PRODUCTOR`, `TECNICO`).
  - `full_name`: Nombre completo del usuario para consumo de interfaz.
- Hashing seguro de contraseñas: Se verifico la operatividad de `passlib` utilizando `argon2id` como algoritmo principal con fallback transparente a `bcrypt`.

### 2.3. Esquemas de Datos: `backend/app/schemas/user.py`
- Esquema `TokenPayload`: Se agregaron los campos opcionales `email` y `full_name` para tipar adecuadamente la informacion obtenida tras la decodificacion del token.
- Compatibilidad con Pydantic v2: Se migraron los parametros deprecados `example` hacia la sintaxis oficial `examples=[...]` en los campos de `UserBase` y `UserCreate`.

### 2.4. Inyeccion de Dependencias: `backend/app/api/deps.py`
- Flujo OAuth2: Se confirmo que `oauth2_scheme` apunta formalmente a `tokenUrl="/api/v1/auth/login"`.
- Validacion de identidad (`get_current_user`):
  - Decodifica el token mediante la clave secreta y algoritmo configurados.
  - Realiza una consulta asincrona a la base de datos mediante SQLAlchemy 2.0 (`select(User).where(User.id == user_uuid)`).
  - Valida el estado activo de la cuenta: si `is_active` es falso, emite una excepcion con codigo HTTP 403 Forbidden y mensaje de detalle `"Usuario inactivo"`.
  - En caso de token corrupto, expirado o usuario inexistente, lanza una excepcion con codigo HTTP 401 Unauthorized y encabezado `WWW-Authenticate: Bearer`.

### 2.5. Controladores de Autenticacion: `backend/app/api/v1/endpoints/auth.py`
- `POST /api/v1/auth/register`:
  - Recibe el esquema `UserCreate` (email, full_name, password, role).
  - Verifica que el correo no este registrado previamente (emite HTTP 400 en caso de duplicidad).
  - Hashea la contraseña con Argon2id.
  - Persiste la entidad en la base de datos aplicando `await db.commit()` y `await db.refresh(new_user)`.
  - Retorna `UserOut` con codigo HTTP 201 Created.
- `POST /api/v1/auth/login`:
  - Recibe credenciales mediante `OAuth2PasswordRequestForm` (`username` correspondiente al correo y `password`).
  - Verifica existencia y valida el hash con `verify_password`.
  - Verifica que el usuario este activo (`is_active is True`).
  - Emite el token JWT con los claims requeridos y retorna el esquema `Token` con codigo HTTP 200 OK.
- `GET /api/v1/auth/me`:
  - Protegido mediante la dependencia `get_current_user`.
  - Retorna los datos del usuario autenticado bajo el esquema `UserOut`.

---

## 3. Integracion con los Modulos de Negocio

La activacion de `api_router` en `main.py` unifico los siguientes modulos existentes bajo el prefijo `/api/v1`:

1. Autenticacion y Usuarios (`/api/v1/auth`):
   - Registro de usuarios, login OAuth2 y perfil del usuario autenticado.
2. Perfil de Productores (`/api/v1/producers`):
   - Creacion, actualizacion y consulta de perfil de productor asociado al usuario en sesion.
3. Fincas Cafetaleras (`/api/v1/farms`):
   - Registro y administracion de fincas vinculadas al perfil de productor autenticado.
4. Parcelas y GIS Espacial (`/api/v1/plots`):
   - Creacion de parcelas con almacenamiento de geometria PostGIS (`Polygon, EPSG:4326`), calculo geodesico de superficie en hectareas y exportacion GeoJSON RFC 7946 para MapLibre GL.

### Proteccion de Endpoints
Los endpoints de productores, fincas y parcelas utilizan la dependencia `get_current_user` y `get_current_producer`, bloqueando el acceso anonimo con respuestas HTTP 401 Unauthorized cuando no se provee un token valido en el encabezado `Authorization: Bearer <token>`.

---

## 4. Pruebas y Validacion

Se construyo una suite de pruebas automatizadas en `backend/tests/test_auth.py` ejecutada mediante `pytest` con un motor SQLite asincrono en memoria (`aiosqlite`), aislando la validacion de dependencias externas.

### 4.1. Resultados de la Suite Automatizada
Se ejecutaron 15 casos de prueba con resultado satisfactorio:

1. `test_password_hashing`: Valida generacion de hash seguro y rechazo de contraseñas incorrectas.
2. `test_jwt_token_generation_and_claims`: Comprueba emision y presencia de claims `sub`, `email`, `role`, `full_name`, `iat`, `exp`.
3. `test_jwt_token_expired`: Comprueba rechazo inmediato de tokens con fecha de expiracion vencida.
4. `test_register_user_success`: Registro de usuario con HTTP 201 Created y exclusion de la contraseña hasheada en la respuesta.
5. `test_register_user_duplicate_email`: Retorno de HTTP 400 Bad Request ante intento de registro con correo ya existente.
6. `test_login_success`: Autenticacion exitosa via formulario OAuth2 y obtencion de token Bearer valido.
7. `test_login_invalid_password`: Rechazo con HTTP 401 Unauthorized ante contraseña incorrecta.
8. `test_login_nonexistent_user`: Rechazo con HTTP 401 Unauthorized ante usuario no registrado.
9. `test_login_inactive_user`: Rechazo con HTTP 403 Forbidden y mensaje "Usuario inactivo".
10. `test_get_me_protected_endpoint`: Consulta exitosa a `/auth/me` con encabezado Bearer.
11. `test_get_me_unauthorized_without_token`: Rechazo con HTTP 401 Unauthorized al omitir token.
12. `test_get_me_invalid_token`: Rechazo con HTTP 401 Unauthorized al enviar token malformado o falso.
13. `test_cross_protection_farms_unauthorized`: Rechazo de peticiones anonimas en `/api/v1/farms`.
14. `test_cross_protection_producers_me_unauthorized`: Rechazo de peticiones anonimas en `/api/v1/producers/me`.
15. `test_cross_protection_plots_unauthorized`: Rechazo de peticiones anonimas en `/api/v1/plots`.

### 4.2. Validacion de Servidor en Vivo y Swagger UI
- Arranque del servidor: Se inicio Uvicorn (`uvicorn app.main:app --reload`) sin errores de importacion circular ni duplicidad de rutas.
- Interfaz interactiva `/docs`: Swagger UI expone el esquema de seguridad `JWT Bearer` (OAuth2 Password Flow con `tokenUrl=/api/v1/auth/login`).
- Boton Authorize: Permite ingresar correo y contraseña para autenticar la sesion y realizar peticiones interactivas a los endpoints protegidos.

---

## 5. Siguientes Pasos para Concluir la Implementacion

Para continuar con el despliegue y desarrollo del proyecto, se recomiendan los siguientes pasos ordenados cronologicamente:

### Paso 1: Inicializacion de la Base de Datos Espacial (PostgreSQL + PostGIS)
1. Levantar el contenedor de base de datos definido en `docker-compose.yml`:
   ```bash
   cd backend
   docker compose up -d db
   ```
2. Ejecutar el script de inicializacion para habilitar las extensiones `uuid-ossp` y `postgis`, crear las tablas del ORM y sembrar al usuario administrador inicial (`admin@cafetrace.sv`):
   ```bash
   cd backend
   python scripts/init_db.py
   ```
3. Verificar la conexion ingresando al endpoint de salud:
   ```bash
   curl http://localhost:8000/health
   ```
   El campo `database` debe retornar `"connected"` y `postgis_version` debe reflejar la version instalada.

### Paso 2: Datos Semilla de Prueba (Seed Data)
1. Generar un script de poblado (`backend/scripts/seed_data.py`) que registre productores de ejemplo, fincas en zonas cafetaleras reconocidas de El Salvador (Apaneca-Ilamatepec, Alotepec-Metapan, Tecapa-Chinameca) y parcelas con coordenadas poligonales reales en formato WGS84 EPSG:4326.
2. Comprobar que los calculos automaticos de hectareas mediante `ST_Area(geometry::geography) / 10000.0` se registren de forma consistente.

### Paso 3: Integracion con el Portal Web (Frontend)
1. Configurar el cliente HTTP (Axios o Fetch wrapper) en la aplicacion para enviar el encabezado `Authorization: Bearer <token>` en todas las peticiones a rutas protegidas.
2. Implementar la persistencia de sesion en el cliente utilizando cookies seguras con atributo `HttpOnly` o almacenamiento seguro con control de ciclo de vida.
3. Crear un interceptor de respuestas para capturar codigos HTTP 401 y redirigir automaticamente al formulario de inicio de sesion cuando la sesion expire.

### Paso 4: Mecanismo de Renovacion de Tokens (Refresh Tokens)
1. Extender el modelo y los endpoints de autenticacion para incluir un token de actualizacion (`refresh_token`) con mayor tiempo de vida, permitiendo renovar el `access_token` sin requerir que el productor o tecnico reingrese sus credenciales con frecuencia.
2. Almacenar el hash o identificador unico del refresh token en la base de datos para habilitar revocacion remota de sesiones.

### Paso 5: Control de Acceso Basado en Roles (RBAC Granular)
1. Aplicar la funcion `require_role(["ADMIN", "TECNICO"])` en operaciones sensibles, tales como aprobacion de expedientes EUDR, eliminacion de parcelas o edicion de perfiles ajenos.
2. Garantizar que los productores unicamente puedan consultar y modificar sus propias fincas y parcelas mediante filtros directos por `producer_id`.
