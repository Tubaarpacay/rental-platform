# -------------------------------------------------
# Kullanıcı İşlemleri
# -------------------------------------------------

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    create_password_reset_expire_time,
    create_password_reset_token,
    create_verification_token,
    get_current_user,
    hash_password,
    is_password_reset_token_expired,
    verify_password
)
from app.database import get_db
from app.email_utils import (
    send_password_reset_email,
    send_verification_email
)
from app.models import User
from app.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserResponse
)


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# -------------------------------------------------
# Kullanıcı Kayıt İşlemi
# -------------------------------------------------
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Yeni kullanıcı oluşturur.

    Kayıt işlemi tamamlandıktan sonra kullanıcıya
    hesap doğrulama e-postası gönderilir.
    """

    # -------------------------------------------------
    # E-posta adresini standartlaştır
    # -------------------------------------------------
    # Büyük/küçük harf ve boşluk farklılıklarının
    # aynı e-posta için ayrı hesap oluşturmasını engeller.
    email = str(user_data.email).strip().lower()

    # -------------------------------------------------
    # E-posta daha önce kullanılmış mı?
    # -------------------------------------------------
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi zaten kayıtlı."
        )

    # -------------------------------------------------
    # Şifreyi hashle ve doğrulama tokenı oluştur
    # -------------------------------------------------
    hashed_password = hash_password(
        user_data.password
    )

    verification_token = create_verification_token()

    # -------------------------------------------------
    # Yeni kullanıcı oluştur
    # -------------------------------------------------
    new_user = User(
        email=email,
        full_name=user_data.full_name.strip(),
        hashed_password=hashed_password,
        is_verified=False,
        verification_token=verification_token
    )

    # -------------------------------------------------
    # Veritabanına kaydet
    # -------------------------------------------------
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # -------------------------------------------------
    # E-posta doğrulama bağlantısını oluştur
    # -------------------------------------------------
    verification_link = (
        "http://127.0.0.1:8000/users/verify-email"
        f"?token={verification_token}"
    )

    # -------------------------------------------------
    # Doğrulama e-postasını arka planda gönder
    # -------------------------------------------------
    background_tasks.add_task(
        send_verification_email,
        receiver_email=new_user.email,
        verification_link=verification_link
    )

    return new_user


# -------------------------------------------------
# E-posta Doğrulama İşlemi
# -------------------------------------------------
@router.get("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    E-posta doğrulama tokenını kontrol eder.

    Token geçerliyse kullanıcının hesabı
    doğrulanmış olarak işaretlenir.
    """

    # -------------------------------------------------
    # Token ile kullanıcıyı bul
    # -------------------------------------------------
    user = db.query(User).filter(
        User.verification_token == token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz doğrulama bağlantısı."
        )

    # -------------------------------------------------
    # Hesabı doğrulanmış olarak güncelle
    # -------------------------------------------------
    user.is_verified = True
    user.verification_token = None

    db.commit()

    return {
        "message": "Email adresiniz başarıyla doğrulandı."
    }


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
    Kullanıcının sisteme giriş yapmasını sağlar.

    Swagger OAuth2 yapısıyla uyumlu olması için
    kullanıcı bilgileri form-data olarak alınır.
    """

    # -------------------------------------------------
    # E-posta adresini standartlaştır
    # -------------------------------------------------
    email = username.strip().lower()

    # -------------------------------------------------
    # Kullanıcıyı bul
    # -------------------------------------------------
    user = db.query(User).filter(
        User.email == email
    ).first()

    # Kullanıcının bulunup bulunmadığı hakkında
    # ayrıntılı bilgi vermeden genel hata döndürülür.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı."
        )

    # -------------------------------------------------
    # Şifreyi doğrula
    # -------------------------------------------------
    if not verify_password(
        password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı."
        )

    # -------------------------------------------------
    # E-posta doğrulanmış mı?
    # -------------------------------------------------
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Giriş yapmadan önce email "
                "adresinizi doğrulamalısınız."
            )
        )

    # -------------------------------------------------
    # JWT access token oluştur
    # -------------------------------------------------
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Kullanıcının e-posta adresine şifre sıfırlama
    bağlantısı gönderilmesini sağlar.

    Güvenlik nedeniyle e-posta kayıtlı olsun veya olmasın
    kullanıcıya aynı cevap döndürülür.
    """

    # -------------------------------------------------
    # E-posta adresini standartlaştır
    # -------------------------------------------------
    email = str(request.email).strip().lower()

    # -------------------------------------------------
    # Kullanıcıyı bul
    # -------------------------------------------------
    user = db.query(User).filter(
        User.email == email
    ).first()

    # E-posta sistemde kayıtlı değilse de aynı mesajı döndür.
    # Böylece sistemde hangi e-postaların kayıtlı olduğu anlaşılmaz.
    if not user:
        return {
            "message": (
                "Eğer bu email adresi kayıtlıysa "
                "şifre sıfırlama bağlantısı gönderildi."
            )
        }

    # -------------------------------------------------
    # Şifre sıfırlama tokenı ve geçerlilik süresi oluştur
    # -------------------------------------------------
    reset_token = create_password_reset_token()
    reset_expires = create_password_reset_expire_time()

    user.reset_password_token = reset_token
    user.reset_password_expires = reset_expires

    db.commit()
    db.refresh(user)

    # -------------------------------------------------
    # Şifre sıfırlama bağlantısını oluştur
    # -------------------------------------------------
    # Frontend geliştirildiğinde bu adres,
    # frontend şifre sıfırlama sayfasıyla değiştirilecek.
    reset_link = (
        "http://127.0.0.1:8000/reset-password"
        f"?token={reset_token}"
    )

    # -------------------------------------------------
    # Şifre sıfırlama e-postasını arka planda gönder
    # -------------------------------------------------
    background_tasks.add_task(
        send_password_reset_email,
        receiver_email=user.email,
        reset_link=reset_link
    )

    return {
        "message": (
            "Eğer bu email adresi kayıtlıysa "
            "şifre sıfırlama bağlantısı gönderildi."
        )
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
    Kullanıcının token ile yeni şifre belirlemesini sağlar.

    Token geçerliyse ve süresi dolmamışsa
    kullanıcının şifresi güncellenir.
    """

    # -------------------------------------------------
    # Token ile kullanıcıyı bul
    # -------------------------------------------------
    user = db.query(User).filter(
        User.reset_password_token == request.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz şifre sıfırlama tokenı."
        )

    # -------------------------------------------------
    # Token süresini kontrol et
    # -------------------------------------------------
    if is_password_reset_token_expired(
        user.reset_password_expires
    ):
        # Süresi dolmuş tokenı temizle
        user.reset_password_token = None
        user.reset_password_expires = None
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Şifre sıfırlama tokenının süresi dolmuş."
        )

    # -------------------------------------------------
    # Yeni şifreyi hashleyerek kaydet
    # -------------------------------------------------
    user.hashed_password = hash_password(
        request.new_password
    )

    # Kullanılan tokenı geçersiz hale getir
    user.reset_password_token = None
    user.reset_password_expires = None

    db.commit()

    return {
        "message": "Şifre başarıyla sıfırlandı."
    }


# -------------------------------------------------
# Giriş Yapan Kullanıcının Bilgileri
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