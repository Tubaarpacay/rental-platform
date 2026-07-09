# -------------------------------------------------
# Para İadesi (Refund) İşlemleri
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
from app.models import (
    Booking,
    Item,
    Notification,
    Payment,
    Refund,
    User
)

# Pydantic şemaları
from app.schemas import (
    RefundCreate,
    RefundResponse
)


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/refunds",
    tags=["Refunds"]
)


# -------------------------------------------------
# Para İadesi Talebi Oluşturma
# -------------------------------------------------
@router.post("/", response_model=RefundResponse)
def create_refund(
    refund_data: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kullanıcının ödeme yaptığı rezervasyon
    için para iadesi talebi oluşturmasını sağlar.
    """

    # -------------------------------------------------
    # Rezervasyonu bul
    # -------------------------------------------------
    booking = db.query(Booking).filter(
        Booking.id == refund_data.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı."
        )

    # -------------------------------------------------
    # Rezervasyon kullanıcıya ait mi?
    # -------------------------------------------------
    if booking.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu rezervasyon için iade talebi oluşturamazsınız."
        )

    # -------------------------------------------------
    # Rezervasyon ödenmiş mi?
    # -------------------------------------------------
    if booking.status != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece ödenmiş rezervasyonlar için iade talebi oluşturulabilir."
        )

    # -------------------------------------------------
    # Ödeme kaydını bul
    # -------------------------------------------------
    payment = db.query(Payment).filter(
        Payment.booking_id == booking.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ödeme kaydı bulunamadı."
        )

    # -------------------------------------------------
    # Aynı rezervasyon için daha önce iade alınmış mı?
    # -------------------------------------------------
    existing_refund = db.query(Refund).filter(
        Refund.booking_id == booking.id
    ).first()

    if existing_refund:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu rezervasyon için daha önce iade talebi oluşturulmuş."
        )

    # -------------------------------------------------
    # İlanı bul
    # -------------------------------------------------
    item = db.query(Item).filter(
        Item.id == booking.item_id
    ).first()

    # -------------------------------------------------
    # Booking durumunu güncelle
    # -------------------------------------------------
    booking.status = "refunded"

    # -------------------------------------------------
    # Refund kaydı oluştur
    # -------------------------------------------------
    refund = Refund(
        booking_id=booking.id,
        payment_id=payment.id,
        user_id=current_user.id,
        amount=payment.amount,
        reason=refund_data.reason,
        status="simulated_refunded"
    )

    # -------------------------------------------------
    # İlan sahibine bildirim oluştur
    # -------------------------------------------------
    notification = Notification(
        user_id=item.owner_id,
        title="İade Talebi",
        message=f"{item.title} ilanınız için para iadesi talebi oluşturuldu."
    )

    # -------------------------------------------------
    # Veritabanına kaydet
    # -------------------------------------------------
    db.add(refund)
    db.add(notification)

    db.commit()
    db.refresh(refund)

    return refund


# -------------------------------------------------
# Kullanıcının İade Taleplerini Listeleme
# -------------------------------------------------
@router.get("/", response_model=list[RefundResponse])
def list_refunds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    oluşturduğu iade taleplerini listeler.
    """

    return db.query(Refund).filter(
        Refund.user_id == current_user.id
    ).order_by(
        Refund.created_at.desc()
    ).all()