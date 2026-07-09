# -------------------------------------------------
# Rezervasyon İşlemleri
# -------------------------------------------------

# FastAPI kütüphaneleri
from fastapi import APIRouter, Depends, HTTPException, status

# SQLAlchemy oturumu
from sqlalchemy.orm import Session

# Veritabanı bağlantısı
from app.database import get_db

# Veritabanı modelleri
from app.models import (
    Booking,
    Item,
    User,
    Address,
    Notification
)

# Pydantic şemaları
from app.schemas import (
    BookingCreate,
    BookingResponse
)

# JWT ile giriş yapan kullanıcıyı almak için
from app.auth import get_current_user


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


# -------------------------------------------------
# Yeni Rezervasyon Oluşturma
# -------------------------------------------------
@router.post("/", response_model=BookingResponse)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    seçtiği ilan için rezervasyon oluşturur.
    """

    # -------------------------------------------------
    # İlan gerçekten var mı kontrol et
    # -------------------------------------------------
    item = db.query(Item).filter(
        Item.id == booking_data.item_id,
        Item.is_active == True
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # -------------------------------------------------
    # Teslimat adresini kontrol et
    # -------------------------------------------------
    if booking_data.address_id is not None:

        address = db.query(Address).filter(
            Address.id == booking_data.address_id
        ).first()

        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adres bulunamadı."
            )

        # Kullanıcı sadece kendi adresini seçebilir
        if address.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu adres size ait değil."
            )

    # -------------------------------------------------
    # Kullanıcı kendi ilanını kiralayamaz
    # -------------------------------------------------
    if item.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi ilanınızı kiralayamazsınız."
        )

    # -------------------------------------------------
    # Tarih kontrolü
    # -------------------------------------------------
    if booking_data.end_date < booking_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitiş tarihi başlangıç tarihinden önce olamaz."
        )

    # -------------------------------------------------
    # Aynı tarihlerde başka rezervasyon var mı?
    # -------------------------------------------------
    overlapping_booking = db.query(Booking).filter(
        Booking.item_id == booking_data.item_id,
        Booking.status != "cancelled",
        Booking.start_date <= booking_data.end_date,
        Booking.end_date >= booking_data.start_date
    ).first()

    if overlapping_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu tarihler arasında ilan zaten rezerve edilmiş."
        )

    # -------------------------------------------------
    # Kiralama süresini hesapla
    # -------------------------------------------------
    rental_days = (
        booking_data.end_date -
        booking_data.start_date
    ).days + 1

    # -------------------------------------------------
    # Toplam fiyatı hesapla
    # -------------------------------------------------
    total_price = item.daily_price * rental_days

    # -------------------------------------------------
    # Yeni rezervasyon oluştur
    # -------------------------------------------------
    new_booking = Booking(
        item_id=item.id,
        renter_id=current_user.id,
        address_id=booking_data.address_id,
        start_date=booking_data.start_date,
        end_date=booking_data.end_date,
        total_price=total_price,
        status="pending"
    )

    # -------------------------------------------------
    # İlan sahibine bildirim oluştur
    # -------------------------------------------------
    notification = Notification(
        user_id=item.owner_id,
        title="Yeni Rezervasyon",
        message=f"{item.title} ilanınız için yeni bir rezervasyon oluşturuldu."
    )

    # -------------------------------------------------
    # Rezervasyonu ve bildirimi kaydet
    # -------------------------------------------------
    db.add(new_booking)
    db.add(notification)

    db.commit()
    db.refresh(new_booking)

    return new_booking


# -------------------------------------------------
# Kullanıcının Rezervasyonlarını Listeleme
# -------------------------------------------------
@router.get("/", response_model=list[BookingResponse])
def list_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    oluşturduğu rezervasyonları listeler.
    """

    return db.query(Booking).filter(
        Booking.renter_id == current_user.id
    ).all()


# -------------------------------------------------
# Rezervasyon İptal Etme
# -------------------------------------------------
@router.put("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    kendi rezervasyonunu iptal etmesini sağlar.
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
    # Kullanıcı sadece kendi rezervasyonunu iptal edebilir
    # -------------------------------------------------
    if booking.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu rezervasyonu iptal etme yetkiniz yok."
        )

    # -------------------------------------------------
    # Rezervasyon zaten iptal edilmiş mi?
    # -------------------------------------------------
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rezervasyon zaten iptal edilmiş."
        )

    # -------------------------------------------------
    # Rezervasyonu iptal et
    # -------------------------------------------------
    booking.status = "cancelled"

    db.commit()
    db.refresh(booking)

    return booking