# ==========================================================
# database.py
#
# Bu dosya uygulamanın PostgreSQL veritabanı ile bağlantısını
# yönetir.
#
# Görevleri:
# - .env dosyasını okumak
# - SQLAlchemy Engine oluşturmak
# - Veritabanı oturumu (Session) oluşturmak
# - Tüm modeller için ortak Base sınıfını oluşturmak
# ==========================================================

# SQLAlchemy bağlantı işlemleri
from sqlalchemy import create_engine

# SQLAlchemy ORM araçları
from sqlalchemy.orm import declarative_base, sessionmaker

# .env dosyasını okumak için
from dotenv import load_dotenv

# Ortam değişkenlerine erişmek için
import os


# ----------------------------------------------------------
# .env dosyasını yükle
# ----------------------------------------------------------
load_dotenv()


# ----------------------------------------------------------
# Veritabanı bağlantı adresini .env dosyasından al
# ----------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")


# ----------------------------------------------------------
# SQLAlchemy Engine oluştur
#
# Engine uygulama ile PostgreSQL arasındaki ana bağlantıdır.
# ----------------------------------------------------------
engine = create_engine(DATABASE_URL)


# ----------------------------------------------------------
# Session (Veritabanı Oturumu)
#
# Her istek geldiğinde yeni bir session oluşturacağız.
# Bu session üzerinden sorgular yapılacak.
# ----------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ----------------------------------------------------------
# Tüm modellerimizin miras alacağı temel sınıf
#
# Örnek:
#
# class User(Base):
#     ...
#
# class Item(Base):
#     ...
# ----------------------------------------------------------
Base = declarative_base()


# ----------------------------------------------------------
# Her API isteği için yeni bir veritabanı oturumu oluşturur.
#
# İş bittikten sonra bağlantıyı otomatik kapatır.
# ----------------------------------------------------------
def get_db():
    """
    Create a new database session for each request.
    """

    # Yeni session oluştur
    db = SessionLocal()

    try:
        # Session'ı endpoint'e gönder
        yield db

    finally:
        # İş bitince bağlantıyı kapat
        db.close()