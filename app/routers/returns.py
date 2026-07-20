# -------------------------------------------------
# Ürün Geri Gönderme / Return İşlemleri
# -------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Booking, Item, Notification, ReturnRequest, User
from app.schemas import ReturnCreate, ReturnResponse


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/returns",
    tags=["Returns"]
)


# -------------------------------------------------
# Ürün Geri Gönderme Talebi Oluşturma
# -------------------------------------------------
@router.post("/", response_model=ReturnResponse)
def create_return_request(
    return_data: ReturnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kiralayan kullanıcının ürünü geri gönderdiğini
    bildirmesini sağlar.
    """

    # -------------------------------------------------
    # Rezervasyonu bul
    # -------------------------------------------------
    booking = db.query(Booking).filter(
        Booking.id == return_data.booking_id
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
            detail="Bu rezervasyon için ürün iadesi oluşturamazsınız."
        )

    # -------------------------------------------------
    # Rezervasyon ödenmiş mi?
    # -------------------------------------------------
    if booking.status != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Sadece ödenmiş rezervasyonlar için "
                "ürün iadesi oluşturulabilir."
            )
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
    # Aynı rezervasyon için daha önce iade talebi var mı?
    # -------------------------------------------------
    existing_return = db.query(ReturnRequest).filter(
        ReturnRequest.booking_id == booking.id
    ).first()

    if existing_return:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Bu rezervasyon için zaten "
                "ürün iade talebi oluşturulmuş."
            )
        )

    # -------------------------------------------------
    # Ürün iade talebi oluştur
    # -------------------------------------------------
    return_request = ReturnRequest(
        booking_id=booking.id,
        renter_id=current_user.id,
        owner_id=item.owner_id,
        cargo_company=return_data.cargo_company,
        tracking_number=return_data.tracking_number,
        note=return_data.note,
        status="return_requested"
    )

    # -------------------------------------------------
    # İlan sahibine bildirim oluştur
    # -------------------------------------------------
    notification = Notification(
        user_id=item.owner_id,
        title="Ürün İade Talebi",
        message=(
            f"{item.title} ilanınız için "
            "ürün geri gönderme talebi oluşturuldu."
        )
    )

    # -------------------------------------------------
    # Veritabanına kaydet
    # -------------------------------------------------
    db.add(return_request)
    db.add(notification)

    db.commit()
    db.refresh(return_request)

    return return_request


# -------------------------------------------------
# Kullanıcının Return Kayıtlarını Listeleme
# -------------------------------------------------
@router.get("/", response_model=list[ReturnResponse])
def list_returns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının kiralayan veya ilan sahibi
    olarak ilgili olduğu ürün iade kayıtlarını listeler.
    """

    return db.query(ReturnRequest).filter(
        (ReturnRequest.renter_id == current_user.id)
        | (ReturnRequest.owner_id == current_user.id)
    ).order_by(
        ReturnRequest.created_at.desc()
    ).all()


# -------------------------------------------------
# İlan Sahibinin Ürün Teslimini Onaylaması
# -------------------------------------------------
@router.put(
    "/{return_id}/confirm",
    response_model=ReturnResponse
)
def confirm_return_request(
    return_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    İlan sahibinin geri gönderilen ürünü
    teslim aldığını onaylamasını sağlar.
    """

    # -------------------------------------------------
    # Ürün iade kaydını bul
    # -------------------------------------------------
    return_request = db.query(ReturnRequest).filter(
        ReturnRequest.id == return_id
    ).first()

    if not return_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ürün iade kaydı bulunamadı."
        )

    # -------------------------------------------------
    # Sadece ilan sahibi onaylayabilir
    # -------------------------------------------------
    if return_request.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ürün iadesini onaylama yetkiniz yok."
        )

    # -------------------------------------------------
    # Yalnızca bekleyen iade talepleri onaylanabilir
    # -------------------------------------------------
    if return_request.status != "return_requested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yalnızca bekleyen ürün iade talepleri onaylanabilir."
        )

    # -------------------------------------------------
    # Rezervasyonu bul
    # -------------------------------------------------
    booking = db.query(Booking).filter(
        Booking.id == return_request.booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rezervasyon bulunamadı."
        )

    # -------------------------------------------------
    # Durumları güncelle
    # -------------------------------------------------
    return_request.status = "received"
    booking.status = "completed"

    # -------------------------------------------------
    # Kiralayan kullanıcıya bildirim oluştur
    # -------------------------------------------------
    notification = Notification(
        user_id=return_request.renter_id,
        title="Ürün Teslim Alındı",
        message=(
            "İlan sahibi ürünü teslim aldığını onayladı. "
            "Kiralama tamamlandı."
        )
    )

    # -------------------------------------------------
    # Veritabanına kaydet
    # -------------------------------------------------
    db.add(notification)

    db.commit()
    db.refresh(return_request)

    return return_request