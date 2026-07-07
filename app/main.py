# -------------------------------------------------
# FastAPI Ana Uygulaması
# -------------------------------------------------

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

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
    notifications
)

# -------------------------------------------------
# FastAPI Uygulaması
# -------------------------------------------------
app = FastAPI(
    title="Eşya Kiralama API",
    version="1.0.0"
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


# -------------------------------------------------
# Ana Sayfa
# -------------------------------------------------
@app.get("/")
def home():
    return {
        "message": "Eşya Kiralama API çalışıyor."
    }


# -------------------------------------------------
# Veritabanı Bağlantı Testi
# -------------------------------------------------
@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )

        return {
            "database": "connected",
            "result": result.scalar()
        }