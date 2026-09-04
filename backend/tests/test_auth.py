import pytest
import pytest_asyncio
from datetime import timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.main import app
from app.models.user import User


# In-memory async SQLite engine for isolated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    """
    Creates tables before each test and drops them afterward.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all, tables=[User.__table__])
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(User.metadata.drop_all, tables=[User.__table__])


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


# ==============================================================================
# 1. PRUEBAS UNITARIAS DE SEGURIDAD
# ==============================================================================

def test_password_hashing():
    plain_password = "CafeSV2026!SecurePassword"
    hashed = get_password_hash(plain_password)
    assert hashed != plain_password
    assert verify_password(plain_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_claims():
    subject = "11111111-2222-3333-4444-555555555555"
    email = "productor@cafetrace.sv"
    role = "PRODUCTOR"
    token = create_access_token(
        subject=subject,
        email=email,
        role=role,
        extra_claims={"full_name": "Juan Pérez"},
    )
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == subject
    assert payload["email"] == email
    assert payload["role"] == role
    assert payload["full_name"] == "Juan Pérez"
    assert "iat" in payload
    assert "exp" in payload


def test_jwt_token_expired():
    token = create_access_token(
        subject="expired-uuid",
        expires_delta=timedelta(seconds=-10),
    )
    payload = decode_access_token(token)
    assert payload is None


# ==============================================================================
# 2. PRUEBAS DE ENDPOINTS DE AUTENTICACIÓN (FastAPI v1)
# ==============================================================================

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    payload = {
        "email": "carlos.ramos@cafetrace.sv",
        "full_name": "Carlos Ramos",
        "password": "Password123!",
        "role": "PRODUCTOR",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert data["role"] == "PRODUCTOR"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_user_duplicate_email(client: AsyncClient):
    payload = {
        "email": "repetido@cafetrace.sv",
        "full_name": "Productor Original",
        "password": "Password123!",
        "role": "PRODUCTOR",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Intento de registrar con el mismo email
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "Ya existe una cuenta" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Primero registramos
    reg_payload = {
        "email": "login.test@cafetrace.sv",
        "full_name": "Login Test User",
        "password": "ValidPassword2026!",
        "role": "TECNICO",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login exitoso usando OAuth2PasswordRequestForm (form-data)
    login_data = {
        "username": "login.test@cafetrace.sv",
        "password": "ValidPassword2026!",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    token_info = response.json()
    assert "access_token" in token_info
    assert token_info["token_type"] == "bearer"
    assert token_info["expires_in"] > 0

    # Validar claims en el token recibido
    decoded = decode_access_token(token_info["access_token"])
    assert decoded is not None
    assert decoded["email"] == "login.test@cafetrace.sv"
    assert decoded["role"] == "TECNICO"
    assert decoded["full_name"] == "Login Test User"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    reg_payload = {
        "email": "user.fail@cafetrace.sv",
        "full_name": "User Fail",
        "password": "CorrectPassword2026!",
        "role": "PRODUCTOR",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_data = {
        "username": "user.fail@cafetrace.sv",
        "password": "WrongPassword!",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert "incorrectos" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    login_data = {
        "username": "noexiste@cafetrace.sv",
        "password": "AnyPassword123!",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient):
    # Crear usuario inactivo directamente en BD
    async with TestingSessionLocal() as session:
        user = User(
            email="inactivo@cafetrace.sv",
            hashed_password=get_password_hash("Password123!"),
            full_name="Usuario Inactivo",
            role="PRODUCTOR",
            is_active=False,
        )
        session.add(user)
        await session.commit()

    login_data = {
        "username": "inactivo@cafetrace.sv",
        "password": "Password123!",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 403
    assert response.json()["detail"] == "Usuario inactivo"


@pytest.mark.asyncio
async def test_get_me_protected_endpoint(client: AsyncClient):
    reg_payload = {
        "email": "me.test@cafetrace.sv",
        "full_name": "Me Test User",
        "password": "MePassword2026!",
        "role": "ADMIN",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": "me.test@cafetrace.sv", "password": "MePassword2026!"},
    )
    token = login_res.json()["access_token"]

    # Acceso con token válido
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "me.test@cafetrace.sv"
    assert user_data["role"] == "ADMIN"
    assert user_data["full_name"] == "Me Test User"


@pytest.mark.asyncio
async def test_get_me_unauthorized_without_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    headers = {"Authorization": "Bearer token_falso_invalido_12345"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


# ==============================================================================
# 3. PRUEBAS DE PROTECCIÓN CRUZADA (Otros módulos)
# ==============================================================================

@pytest.mark.asyncio
async def test_cross_protection_farms_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/farms")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cross_protection_producers_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/producers/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cross_protection_plots_unauthorized(client: AsyncClient):
    response = await client.post("/api/v1/plots", json={})
    assert response.status_code == 401
