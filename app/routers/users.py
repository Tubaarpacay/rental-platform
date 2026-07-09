# Kullanıcı işlemleri için router dosyası

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    create_password_reset_token,
    create_password_reset_expire_time,
    is_password_reset_token_expired
)
from app.email_utils import send_password_reset_email

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

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı."
        )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )

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

    user = db.query(User).filter(
        User.email == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı."
        )

    if not verify_password(
        password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı."
        )

    access_token = create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# -------------------------------------------------
# Şifremi Unuttum İşlemi
# -------------------------------------------------
@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Kullanıcı e-posta adresini gönderir.

    Güvenlik nedeniyle email sistemde kayıtlı olsa da olmasa da
    aynı mesaj döndürülür. Böylece sistemde hangi e-postaların
    kayıtlı olduğu dışarıdan anlaşılamaz.
    """

    user = db.query(User).filter(
        User.email == request.email
    ).first()

    if not user:
        return {
            "message": "Eğer bu email adresi kayıtlıysa şifre sıfırlama bağlantısı gönderildi."
        }

    reset_token = create_password_reset_token()
    reset_expires = create_password_reset_expire_time()

    user.reset_password_token = reset_token
    user.reset_password_expires = reset_expires

    db.commit()
    db.refresh(user)

    reset_link = f"http://127.0.0.1:8000/reset-password?token={reset_token}"

    send_password_reset_email(
        receiver_email=user.email,
        reset_link=reset_link
    )

    return {
        "message": "Eğer bu email adresi kayıtlıysa şifre sıfırlama bağlantısı gönderildi."
    }


# -------------------------------------------------
# Şifre Sıfırlama İşlemi
# -------------------------------------------------
@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Kullanıcı token ve yeni şifre gönderir.
    Token doğruysa ve süresi geçmediyse şifre güncellenir.
    """

    user = db.query(User).filter(
        User.reset_password_token == request.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz şifre sıfırlama token'ı."
        )

    if is_password_reset_token_expired(
        user.reset_password_expires
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Şifre sıfırlama token'ının süresi dolmuş."
        )

    user.hashed_password = hash_password(
        request.new_password
    )

    user.reset_password_token = None
    user.reset_password_expires = None

    db.commit()

    return {
        "message": "Şifre başarıyla sıfırlandı."
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