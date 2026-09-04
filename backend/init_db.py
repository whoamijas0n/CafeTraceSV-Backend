import asyncio
from sqlalchemy import text
from app.core.config import settings
from app.db.session import async_engine
from app.db.base import Base

# Import models to register them with Base.metadata
from app.models import user, producer, farm, plot

async def init_db():
    print("🚀 Iniciando creación de tablas en la base de datos...")
    try:
        async with async_engine.begin() as conn:
            # Asegurarnos de que PostGIS esté activo antes de crear tablas
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            print("✅ Extensión PostGIS verificada/activada.")

            # Crear todas las tablas definidas en los modelos
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Todas las tablas han sido creadas exitosamente.")

    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
