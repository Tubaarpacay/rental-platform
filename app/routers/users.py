# Kullanıcı işlemleri için router dosyası

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# -------------------------------------------------
# Kullanıcı Kayıt İşlemi
# -------------------------------------------------
@router.post("/register", response_model=UserResponse)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni kullanıcı oluşturur.
    """

    # Aynı email daha önce kayıt olmuş mu kontrol et
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    # Eğer email kayıtlıysa hata döndür
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı."
        )

    # Şifreyi güvenli şekilde hashle
    hashed_password = hash_password(user_data.password)

    # Yeni kullanıcı oluştur
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )

    # Veritabanına kaydet
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# -------------------------------------------------
# Kullanıcı Giriş İşlemi
# -------------------------------------------------
@router.post("/login")
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının giriş yapmasını sağlar.
    Swagger OAuth2 ile uyumlu şekilde form-data kullanır.
    """

    # Email'e göre kullanıcıyı bul
    user = db.query(User).filter(
        User.email == username
    ).first()

    # Kullanıcı bulunamadıysa hata döndür
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı."
        )

    # Şifre yanlışsa hata döndür
    if not verify_password(
        password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı."
        )

    # JWT Access Token oluştur
    access_token = create_access_token(
        data={"sub": user.email}
    )

    # Token'ı kullanıcıya döndür
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# -------------------------------------------------
# Giriş yapan kullanıcı bilgileri
# -------------------------------------------------
@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    JWT token kullanarak giriş yapan
    kullanıcının bilgilerini döndürür.
    """

    return current_user