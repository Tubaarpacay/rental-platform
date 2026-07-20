# -------------------------------------------------
# Bildirim İşlemleri
# -------------------------------------------------

# FastAPI kütüphaneleri
from fastapi import APIRouter, Depends, HTTPException, status

# SQLAlchemy oturumu
from sqlalchemy.orm import Session

# JWT ile giriş yapan kullanıcıyı almak için
from app.auth import get_current_user

# Veritabanı bağlantısı
from app.database import get_db

# Veritabanı modelleri
from app.models import Notification, User

# Pydantic şemaları
from app.schemas import NotificationResponse


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# -------------------------------------------------
# Bildirimleri Listeleme
# -------------------------------------------------
@router.get("/", response_model=list[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    bildirimlerini listeler.
    """

    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()


# -------------------------------------------------
# Bildirimi Okundu Yapma
# -------------------------------------------------
@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    kendi bildirimini okundu olarak işaretlemesini sağlar.
    """

    # Bildirimi bul
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bildirim bulunamadı."
        )

    # Kullanıcı sadece kendi bildirimini güncelleyebilir
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu bildirimi güncelleme yetkiniz yok."
        )
    # Bildirim zaten okunmuş mu?
    if notification.is_read:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu bildirim zaten okunmuş."
        )
    # Okundu olarak işaretle
    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification