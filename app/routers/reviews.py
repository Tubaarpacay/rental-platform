# -------------------------------------------------
# Yorum ve Puanlama İşlemleri
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
from app.models import Booking, Item, Review, User

# Pydantic şemaları
from app.schemas import ReviewCreate, ReviewResponse


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)


# -------------------------------------------------
# Yorum ve Puan Ekleme
# -------------------------------------------------
@router.post("/", response_model=ReviewResponse)
def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının,
    tamamlanan veya ödemesi yapılmış rezervasyon için
    yorum ve puan vermesini sağlar.
    """

    # Rezervasyonu bul
    booking = db.query(Booking).filter(
        Booking.id == review_data.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı."
        )

    # İlanı bul
    item = db.query(Item).filter(
        Item.id == booking.item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # Sadece kiralayan veya ilan sahibi yorum yapabilir
    if current_user.id not in [
        booking.renter_id,
        item.owner_id
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu rezervasyon için yorum yapma yetkiniz yok."
        )

    # İptal edilmiş rezervasyona yorum yapılamaz
    if booking.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="İptal edilmiş rezervasyona yorum yapılamaz."
        )

    # Ödeme yapılmamış rezervasyona yorum yapılmasın
    if booking.status not in ["paid", "completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Yorum yapabilmek için rezervasyonun "
                "ödenmiş veya tamamlanmış olması gerekir."
            )
        )

    # Aynı kullanıcı aynı rezervasyona ikinci kez yorum yapamasın
    existing_review = db.query(Review).filter(
        Review.booking_id == booking.id,
        Review.reviewer_id == current_user.id
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu rezervasyon için zaten yorum yaptınız."
        )

    # Yorum yapılacak kullanıcıyı belirle
    if current_user.id == booking.renter_id:
        reviewed_user_id = item.owner_id
    else:
        reviewed_user_id = booking.renter_id

    # Yeni yorum oluştur
    new_review = Review(
        booking_id=booking.id,
        reviewer_id=current_user.id,
        reviewed_user_id=reviewed_user_id,
        item_id=item.id,
        rating=review_data.rating,
        comment=review_data.comment
    )

    # Veritabanına kaydet
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


# -------------------------------------------------
# İlan Yorumlarını Listeleme
# -------------------------------------------------
@router.get(
    "/item/{item_id}",
    response_model=list[ReviewResponse]
)
def list_item_reviews(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    Belirli bir ilana ait tüm yorumları listeler.
    """

    return db.query(Review).filter(
        Review.item_id == item_id
    ).order_by(
        Review.created_at.desc()
    ).all()