from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import (
    auth_router,
    users_router,
    medicines_router,
    orders_router,
    notifications_router,
)

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RxCompute API",
    description="AI-Powered Pharmacy Management System — Backend API",
    version="1.0.0",
)

# CORS — allow Flutter app on any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(medicines_router)
app.include_router(orders_router)
app.include_router(notifications_router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "RxCompute API", "version": "1.0.0"}
