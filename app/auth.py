# Tarih ve saat işlemleri için gerekli kütüphaneler
from datetime import datetime, timedelta, timezone

# JWT oluşturma ve doğrulama işlemleri için
from jose import jwt, JWTError

# Şifreleri güvenli şekilde hash'lemek için
from passlib.context import CryptContext

# FastAPI güvenlik bileşenleri
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# SQLAlchemy oturumu
from sqlalchemy.orm import Session

# .env dosyasındaki değişkenleri okumak için
from dotenv import load_dotenv

# Ortam değişkenlerine erişmek için
import os

# Veritabanı bağlantısı
from app.database import get_db

# User modeli
from app.models import User

# .env dosyasını yükle
load_dotenv()

# JWT ayarlarını .env dosyasından al
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
)

# Swagger'ın JWT token istemesi için
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/login"
)

# Bcrypt algoritmasını kullanacak şifre yöneticisini oluştur
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """
    Kullanıcının düz metin şifresini güvenli şekilde hash'ler.
    Veritabanına hiçbir zaman gerçek şifre kaydedilmez.
    """

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kullanıcının girdiği şifre ile
    veritabanındaki hash'lenmiş şifreyi karşılaştırır.

    Doğruysa True,
    yanlışsa False döndürür.
    """

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(data: dict):
    """
    Kullanıcı başarılı giriş yaptıktan sonra
    JWT Access Token oluşturur.
    """

    # Gelen veriyi kopyala
    to_encode = data.copy()

    # Token'ın son kullanma tarihini hesapla
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Son kullanma tarihini token içine ekle
    to_encode.update({"exp": expire})

    # JWT token üret ve geri döndür
    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    JWT token içerisindeki email bilgisine göre
    giriş yapan kullanıcıyı veritabanından bulur.
    """

    # Kimlik doğrulama hatası
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # JWT token'ı çöz
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Email bilgisini al
        email = payload.get("sub")

        if email is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Kullanıcıyı veritabanında ara
    user = db.query(User).filter(
        User.email == email
    ).first()

    if user is None:
        raise credentials_exception

    return user