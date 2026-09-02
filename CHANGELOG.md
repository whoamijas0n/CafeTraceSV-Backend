POR FAVOR NO LEER EN DISEÑO .MD

Cambios generales:
Se limpio un poco lo que seria el main donde se ejecuta la app u server.
Se ha creado un .Venv para el desarollo sin romper dependencias
Main con rutas de ejemplo para el uso API

- Se necesita una limpieza en la estrcutura bestial de archivos

Consideraciones:

La bd esta bien estrcuturada por que lo que puede dar luz verde a que paco empieze a recrearla pero con el matiz de optimizar los tipos de datos lo mas posible.

En el caso de conexion con python podemos usar psycopg2-binary

Seria similar a como se trabaja en node por lo que paco y yo estaremos al tanto, en el caso de lectura de datos get lo mejor seria usar vistas o procedimientos almacenados 

En el caso de login un procedimiento donde en codigo se valida el jwt o token de entrada 

Doy luz verde al frontend para empezar con el diseño desde ahora

Resumen del flujo de la app por ahora:

1. Productor se registra y inicia sesión
2. Crea su finca
3. En el mapa, dibuja los polígonos de sus parcelas
4. El sistema guarda el polígono en PostGIS y calcula el área
5. Registra sus cosechas por parcela
6. Crea lotes con código QR
7. El sistema evalúa si está listo para EUDR y predice la deforestacion durante el proceso
8. Exporta archivo GeoJSON con todo
9. El comprador europeo escanea el QR o recibe el archivo
10. ¡Validación de trazabilidad completa! 

ATENCION:
Esto el qr es publico para cualquier persona por lo que se toma en consideracion usuarios normales.
Al escanear el QR → Muestra:
├── Productor: Juan Pérez
├── Finca: Finca El Espino
├── Ubicación: Usulután, Jucuapa
├── Parcela: Tablón Los Cedros
├── Variedad: Bourbon
├── Área: 3.72 hectáreas
├── Cosecha: 15/01/2026
├── Peso: 1,500 kg
├── Proceso: Lavado
└── Puntaje: 86.5 puntos

Integracion con de deforestacion:
Requisitos datos necesarios para guardar y considerar si es necesario tabla o campos de una finca.

Se puede integrar continuamente una vez se tenga el crud para las fincas necesarias. asi se vuelve un proceso en segundo plano que necesita tomar en cuenta el tiempo de tardia en segundo plano.

