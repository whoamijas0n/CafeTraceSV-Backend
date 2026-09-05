from fastapi import APIRouter
from app.api.v1.endpoints import auth, coffee_lots, farms, harvests, organizations, plots, producers, trace

api_router = APIRouter()

# Group all module endpoints with semantic OpenAPI tags
api_router.include_router(
    organizations.router,
    prefix="/organizations",
    tags=["0. Organizaciones (Tenants)"],
)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["1. Autenticación & Usuarios"],
)
api_router.include_router(
    producers.router,
    prefix="/producers",
    tags=["2. Perfil de Productores"],
)
api_router.include_router(
    farms.router,
    prefix="/farms",
    tags=["3. Fincas Cafetaleras"],
)
api_router.include_router(
    plots.router,
    prefix="/plots",
    tags=["4. Parcelas & GIS Espacial"],
)
api_router.include_router(
    harvests.router,
    prefix="/harvests",
    tags=["5. Cosechas"],
)
api_router.include_router(
    coffee_lots.router,
    prefix="/coffee-lots",
    tags=["6. Lotes de Café"],
)
api_router.include_router(
    trace.router,
    prefix="/trace",
    tags=["7. Trazabilidad Pública (QR)"],
)
