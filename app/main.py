# -------------------------------------------------
# FastAPI Ana Uygulaması
# -------------------------------------------------

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from app import pages

from app.database import engine

from app.routers import (
    users,
    categories,
    items,
    bookings,
    payments,
    addresses,
    messages,
    reviews,
    favorites,
    notifications,
    refunds,
    returns,
    offers
)


# -------------------------------------------------
# Log Ayarları
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


# -------------------------------------------------
# FastAPI Uygulaması
# -------------------------------------------------
app = FastAPI(
    title="Eşya Kiralama API",
    description=(
        "Kullanıcıların eşya ilanı oluşturabildiği, "
        "rezervasyon ve teklif verebildiği kiralama platformu API'si."
    ),
    version="1.0.0"
)


# -------------------------------------------------
# Jinja2 Şablon Ayarları
# -------------------------------------------------
templates = Jinja2Templates(
    directory="app/templates"
)


# -------------------------------------------------
# Global Exception Handler
# -------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    error: Exception
):
    """
    Uygulamada yakalanmayan beklenmedik hataları kaydeder
    ve kullanıcıya güvenli, genel bir hata mesajı döndürür.

    Hatanın teknik ayrıntıları kullanıcıya gösterilmez.
    Ayrıntılar yalnızca terminal loguna yazılır.
    """

    logger.exception(
        "Beklenmeyen hata oluştu. Method: %s, URL: %s",
        request.method,
        request.url
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Beklenmeyen bir sunucu hatası oluştu."
        }
    )


# -------------------------------------------------
# Statik Dosyalar
# -------------------------------------------------
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


# -------------------------------------------------
# Uploads Klasörü
# -------------------------------------------------
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# -------------------------------------------------
# Routerlar
# -------------------------------------------------
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(items.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(addresses.router)
app.include_router(messages.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(notifications.router)
app.include_router(refunds.router)
app.include_router(returns.router)
app.include_router(offers.router)
app.include_router(pages.router)


# -------------------------------------------------
# Ana Sayfa
# -------------------------------------------------
@app.get("/")
def home():
    """
    API'nin çalışıp çalışmadığını gösteren ana endpoint.
    """

    return {
        "message": "Eşya Kiralama API çalışıyor."
    }


# -------------------------------------------------
# Veritabanı Bağlantı Testi
# -------------------------------------------------
@app.get("/db-test")
def db_test():
    """
    PostgreSQL veritabanı bağlantısını test eder.
    """

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )

        return {
            "database": "connected",
            "result": result.scalar()
        }