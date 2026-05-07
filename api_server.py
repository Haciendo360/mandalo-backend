import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Rutas Modulares
from mandalo_app.routes.kyc_routes import router as kyc_router
from mandalo_app.routes.location_routes import router as loc_router
from mandalo_app.routes.orders_routes import router as order_router
from mandalo_app.routes.finance_routes import router as finance_router

app_fastapi = FastAPI(
    title="MANDALO API PWA",
    description="API Gateway que orquesta validaciones KYC y enrutamiento Geoespacial Asíncrono"
)

# Configurar middleware para comunicación con UI (Localhost testing)
app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción filtrar este array a la URL de vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectar routers
app_fastapi.include_router(kyc_router)
app_fastapi.include_router(loc_router)
app_fastapi.include_router(order_router)
app_fastapi.include_router(finance_router)

if __name__ == "__main__":
    uvicorn.run("api_server:app_fastapi", host="0.0.0.0", port=8080, reload=True)
