# CaféTrace SV — dev

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