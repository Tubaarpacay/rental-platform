# -------------------------------------------------
# Mesaj İşlemleri
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
from app.models import Booking, Item, Message, Notification, User

# Pydantic şemaları
from app.schemas import (
    MessageCreate,
    MessageResponse
)


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/messages",
    tags=["Messages"]
)


# -------------------------------------------------
# Yeni Mesaj Gönderme
# -------------------------------------------------
@router.post("/", response_model=MessageResponse)
def send_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rezervasyona bağlı olarak
    yeni mesaj gönderir.
    """

    # -------------------------------------------------
    # Rezervasyon var mı kontrol et
    # -------------------------------------------------
    booking = db.query(Booking).filter(
        Booking.id == message_data.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı."
        )

    # -------------------------------------------------
    # İlanı bul
    # -------------------------------------------------
    item = db.query(Item).filter(
        Item.id == booking.item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # -------------------------------------------------
    # Mesajı sadece kiralayan veya ilan sahibi gönderebilir
    # -------------------------------------------------
    if current_user.id not in [
        booking.renter_id,
        item.owner_id
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu sohbet için yetkiniz bulunmuyor."
        )

    # -------------------------------------------------
    # Mesaj alıcısı sadece kiralayan veya ilan sahibi olabilir
    # -------------------------------------------------
    if message_data.receiver_id not in [
        booking.renter_id,
        item.owner_id
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz alıcı."
        )

    # -------------------------------------------------
    # Kullanıcı kendine mesaj gönderemez
    # -------------------------------------------------
    if message_data.receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendinize mesaj gönderemezsiniz."
        )

    # -------------------------------------------------
    # Yeni mesaj oluştur
    # -------------------------------------------------
    new_message = Message(
        booking_id=booking.id,
        sender_id=current_user.id,
        receiver_id=message_data.receiver_id,
        message=message_data.message
    )

    # -------------------------------------------------
    # Mesaj alıcısı için bildirim oluştur
    # -------------------------------------------------
    notification = Notification(
        user_id=message_data.receiver_id,
        title="Yeni Mesaj",
        message="Bir rezervasyon sohbetinde yeni mesajınız var."
    )

    # -------------------------------------------------
    # Mesajı ve bildirimi veritabanına kaydet
    # -------------------------------------------------
    db.add(new_message)
    db.add(notification)
    db.commit()
    db.refresh(new_message)

    return new_message


# -------------------------------------------------
# Rezervasyona Ait Mesajları Listeleme
# -------------------------------------------------
@router.get(
    "/{booking_id}",
    response_model=list[MessageResponse]
)
def get_messages(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rezervasyona ait
    tüm mesajları listeler.
    """

    # -------------------------------------------------
    # Rezervasyonu bul
    # -------------------------------------------------
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı."
        )

    # -------------------------------------------------
    # İlanı bul
    # -------------------------------------------------
    item = db.query(Item).filter(
        Item.id == booking.item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # -------------------------------------------------
    # Sadece kiralayan veya ilan sahibi görebilir
    # -------------------------------------------------
    if current_user.id not in [
        booking.renter_id,
        item.owner_id
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu sohbeti görüntüleme yetkiniz yok."
        )

    # -------------------------------------------------
    # Mesajları getir
    # -------------------------------------------------
    return db.query(Message).filter(
        Message.booking_id == booking_id
    ).order_by(
        Message.created_at.asc()
    ).all()