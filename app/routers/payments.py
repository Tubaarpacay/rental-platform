# -------------------------------------------------
# Ödeme Simülasyonu İşlemleri
# -------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Booking, Item, Notification, Payment, User
from app.schemas import PaymentCreate, PaymentResponse


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


# -------------------------------------------------
# Demo Ödeme Oluşturma
# -------------------------------------------------
@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Demo ödeme işlemi oluşturur.
    Gerçek ödeme alınmaz.

    Test kartı:
    4242424242424242

    Bu kart numarası başarılı ödeme olarak kabul edilir.
    Diğer geçerli kart numaraları başarısız ödeme olarak kaydedilir.
    """

    # -------------------------------------------------
    # Rezervasyonu bul
    # -------------------------------------------------
    booking = db.query(Booking).filter(
        Booking.id == payment_data.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı."
        )

    # -------------------------------------------------
    # Sadece rezervasyonu oluşturan kullanıcı ödeme yapabilir
    # -------------------------------------------------
    if booking.renter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu rezervasyon için ödeme yapma yetkiniz yok."
        )

    # -------------------------------------------------
    # İptal edilmiş rezervasyona ödeme yapılamaz
    # -------------------------------------------------
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İptal edilmiş rezervasyon için ödeme yapılamaz."
        )

    # -------------------------------------------------
    # Ödenmiş rezervasyona tekrar ödeme yapılamaz
    # -------------------------------------------------
    if booking.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu rezervasyon için ödeme zaten yapılmış."
        )

    # -------------------------------------------------
    # Rezervasyonun bağlı olduğu ilanı bul
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
    # Kart numarasını temizle
    # -------------------------------------------------
    # Kullanıcı kart numarasını boşluklu veya tireli yazabilir.
    # Örnek:
    # 4242 4242 4242 4242
    # 4242-4242-4242-4242
    normalized_card_number = (
        payment_data.card_number
        .replace(" ", "")
        .replace("-", "")
    )

    # -------------------------------------------------
    # Kart numarasını doğrula
    # -------------------------------------------------
    if (
        not normalized_card_number.isdigit()
        or len(normalized_card_number) != 16
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kart numarası 16 rakamdan oluşmalıdır."
        )

    # -------------------------------------------------
    # Demo ödeme sonucunu belirle
    # -------------------------------------------------
    # 4242424242424242 başarılı kabul edilir.
    if normalized_card_number == "4242424242424242":
        payment_status = "simulated_success"
        booking.status = "paid"

        # Ödeme başarılı olunca ilan sahibine bildirim oluştur
        notification = Notification(
            user_id=item.owner_id,
            title="Ödeme Tamamlandı",
            message=(
                f"{item.title} ilanınız için ödeme "
                "başarıyla tamamlandı."
            )
        )

        db.add(notification)

    else:
        payment_status = "simulated_failed"

    # -------------------------------------------------
    # Ödeme kaydını oluştur
    # -------------------------------------------------
    # Gerçek kart numarası veya CVV veritabanında saklanmaz.
    # Sadece kart numarasının son dört hanesi tutulur.
    payment = Payment(
        booking_id=booking.id,
        user_id=current_user.id,
        amount=booking.total_price,
        status=payment_status,
        card_last_four=normalized_card_number[-4:]
    )

    # -------------------------------------------------
    # Veritabanına kaydet
    # -------------------------------------------------
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment