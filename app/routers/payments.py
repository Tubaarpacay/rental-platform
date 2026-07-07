# Ödeme simülasyonu işlemleri

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Booking, Payment, User
from app.schemas import PaymentCreate, PaymentResponse


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Demo ödeme işlemi oluşturur.
    Gerçek ödeme alınmaz.
    """

    booking = db.query(Booking).filter(
        Booking.id == payment_data.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı."
        )

    if booking.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu rezervasyon için ödeme yapma yetkiniz yok."
        )

    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İptal edilmiş rezervasyon için ödeme yapılamaz."
        )

    if booking.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu rezervasyon için ödeme zaten yapılmış."
        )

    # Demo ödeme kuralı:
    # 4242424242424242 başarılı kabul edilir.
    if payment_data.card_number == "4242424242424242":
        payment_status = "simulated_success"
        booking.status = "paid"
    else:
        payment_status = "simulated_failed"

    payment = Payment(
        booking_id=booking.id,
        user_id=current_user.id,
        amount=booking.total_price,
        status=payment_status,
        card_last_four=payment_data.card_number[-4:]
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment