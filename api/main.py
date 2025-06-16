"""
FastAPI backend for the LangGraph Sales/Inventory System - Database Version.

Now powered by SQLAlchemy and async database operations.
"""

import logging
import os
import sys
import traceback

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.dirname(__file__))

# Import database configuration
from database import close_database, init_database
from routers.analytics_router import router as analytics_router

# Import routers
from routers.auth_router import router as auth_router
from routers.chat_router import router as chat_router
from routers.inventory_router import router as inventory_router
from routers.sales_router import router as sales_router


app = FastAPI(
    title="LangGraph Sales/Inventory API - Database",
    description="Database-powered API for LangGraph sales and inventory analysis",
    version="3.0.0",
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.render\.com|https://.*\.railway\.app|https://.*\.netlify\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(inventory_router)
app.include_router(sales_router)
app.include_router(analytics_router)


# Add custom error handler
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500, content={"detail": f"Chat processing error: {str(e)}"}
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LangGraph Sales/Inventory API - Database Version",
        "version": "3.0.0",
        "status": "healthy",
        "endpoints": {
            "auth": {
                "register": "/auth/register",
                "login": "/auth/login",
                "me": "/auth/me",
            },
            "chat": "/chat",
            "inventory": {
                "add_product": "/inventory/add-product",
                "list": "/inventory/list",
                "update_stock": "/inventory/update-stock",
                "products_with_stock": "/inventory/products-with-stock",
            },
            "sales": {
                "create_order": "/sales/create-order-with-inventory-sync",
                "status": "/sales/status",
                "debug": "/sales/debug/data",
            },
            "analytics": {
                "analyze": "/analyze",
                "workflows": "/workflows",
                "status": "/status",
            },
        },
        "features": [
            "Autenticación JWT",
            "Chat de lenguaje natural",
            "Gestión de inventario con base de datos",
            "Órdenes de venta con sincronización",
            "Análisis de IA con gráficas",
            "Arquitectura con SQLAlchemy",
            "Operaciones asíncronas",
        ],
    }


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("🚀 Starting LangGraph Sales/Inventory API - Database Version")

    # Initialize database
    try:
        await init_database()
        logger.info("📊 Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    logger.info("✅ API startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("🔻 Shutting down API...")
    await close_database()
    logger.info("✅ API shutdown completed")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
